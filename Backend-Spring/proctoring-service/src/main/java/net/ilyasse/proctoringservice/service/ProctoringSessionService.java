package net.ilyasse.proctoringservice.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.ilyasse.proctoringservice.dto.*;
import net.ilyasse.proctoringservice.entity.FraudEvent;
import net.ilyasse.proctoringservice.entity.ProctoringSession;
import net.ilyasse.proctoringservice.enums.SessionStatus;
import net.ilyasse.proctoringservice.kafka.FraudEventKafkaProducer;
import net.ilyasse.proctoringservice.repository.FraudEventRepository;
import net.ilyasse.proctoringservice.repository.ProctoringSessionRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class ProctoringSessionService {

    private final ProctoringSessionRepository sessionRepository;
    private final FraudEventRepository fraudEventRepository;
    private final FraudEventKafkaProducer kafkaProducer;
    private final StringRedisTemplate redisTemplate;

    private static final String FRAUD_SCORE_KEY = "fraud:score:";
    private static final String DEVICE_KEY = "fraud:device:";

    @Value("${proctoring.fraud.score.threshold:80}")
    private int fraudScoreThreshold;

    // --- Session management ---

    public ProctoringSessionResponse startSession(StartSessionRequest request) {
        ProctoringSession session = ProctoringSession.builder()
                .studentId(request.getStudentId())
                .examId(request.getExamId())
                .attemptId(request.getAttemptId())
                .deviceFingerprint(request.getDeviceFingerprint())
                .status(SessionStatus.IN_PROGRESS)
                .fraudScore(0)
                .build();

        session = sessionRepository.save(session);

        // Store initial fraud score and device fingerprint in Redis
        redisTemplate.opsForValue().set(FRAUD_SCORE_KEY + session.getId(), "0");
        if (request.getDeviceFingerprint() != null) {
            redisTemplate.opsForValue().set(DEVICE_KEY + session.getId(), request.getDeviceFingerprint());
        }

        log.info("[Session] Started session={} student={} exam={}", session.getId(), session.getStudentId(), session.getExamId());
        return toSessionResponse(session);
    }

    public ProctoringSessionResponse endSession(UUID sessionId) {
        ProctoringSession session = getSessionOrThrow(sessionId);
        session.setEndedAt(LocalDateTime.now());
        if (session.getStatus() == SessionStatus.IN_PROGRESS) {
            session.setStatus(SessionStatus.COMPLETED);
        }
        // Sync final fraud score from Redis
        String redisScore = redisTemplate.opsForValue().get(FRAUD_SCORE_KEY + sessionId);
        if (redisScore != null) {
            session.setFraudScore(Integer.parseInt(redisScore));
        }
        sessionRepository.save(session);

        // Clean up Redis
        redisTemplate.delete(FRAUD_SCORE_KEY + sessionId);
        redisTemplate.delete(DEVICE_KEY + sessionId);

        log.info("[Session] Ended session={} status={} score={}", sessionId, session.getStatus(), session.getFraudScore());
        return toSessionResponse(session);
    }

    // --- Fraud event processing ---

    public FraudEventResponse reportFraudEvent(FraudEventRequest request) {
        ProctoringSession session = getSessionOrThrow(request.getSessionId());

        if (session.getStatus() == SessionStatus.COMPLETED) {
            throw new IllegalStateException("Cannot report fraud event on a completed session");
        }

        // Check device fingerprint mismatch if applicable
        if (request.getEventType().name().equals("DEVICE_MISMATCH")) {
            String storedDevice = redisTemplate.opsForValue().get(DEVICE_KEY + request.getSessionId());
            log.warn("[FraudEvent] Device mismatch detected session={} storedDevice={}", request.getSessionId(), storedDevice);
        }

        FraudEvent event = FraudEvent.builder()
                .sessionId(request.getSessionId())
                .studentId(session.getStudentId())
                .examId(session.getExamId())
                .eventType(request.getEventType())
                .confidenceScore(request.getConfidenceScore())
                .details(request.getDetails())
                .build();

        event = fraudEventRepository.save(event);

        // Update fraud score in Redis
        int scoreIncrement = calculateScoreIncrement(request.getConfidenceScore());
        Long newScore = redisTemplate.opsForValue().increment(FRAUD_SCORE_KEY + request.getSessionId(), scoreIncrement);

        // Publish to Kafka
        kafkaProducer.publishFraudEvent(event);

        // Check if session should be flagged
        if (newScore != null && newScore >= fraudScoreThreshold && session.getStatus() == SessionStatus.IN_PROGRESS) {
            session.setStatus(SessionStatus.FLAGGED);
            session.setFraudScore(newScore.intValue());
            sessionRepository.save(session);
            kafkaProducer.publishSessionFlagged(event, newScore.intValue());
            log.warn("[Session] FLAGGED session={} score={}", session.getId(), newScore);
        } else if (newScore != null) {
            // Periodically sync score to DB
            session.setFraudScore(newScore.intValue());
            sessionRepository.save(session);
        }

        return toFraudEventResponse(event);
    }

    // --- Query methods ---

    @Transactional(readOnly = true)
    public ProctoringSessionResponse getSession(UUID sessionId) {
        return toSessionResponse(getSessionOrThrow(sessionId));
    }

    @Transactional(readOnly = true)
    public List<ProctoringSessionResponse> getSessionsByStudent(UUID studentId) {
        return sessionRepository.findByStudentId(studentId)
                .stream().map(this::toSessionResponse).toList();
    }

    @Transactional(readOnly = true)
    public List<ProctoringSessionResponse> getSessionsByExam(UUID examId) {
        return sessionRepository.findByExamId(examId)
                .stream().map(this::toSessionResponse).toList();
    }

    @Transactional(readOnly = true)
    public List<ProctoringSessionResponse> getFlaggedSessions() {
        return sessionRepository.findByStatus(SessionStatus.FLAGGED)
                .stream().map(this::toSessionResponse).toList();
    }

    @Transactional(readOnly = true)
    public List<FraudEventResponse> getEventsBySession(UUID sessionId) {
        return fraudEventRepository.findBySessionIdOrderByDetectedAtDesc(sessionId)
                .stream().map(this::toFraudEventResponse).toList();
    }

    @Transactional(readOnly = true)
    public Integer getLiveFraudScore(UUID sessionId) {
        String score = redisTemplate.opsForValue().get(FRAUD_SCORE_KEY + sessionId);
        return score != null ? Integer.parseInt(score) : 0;
    }

    // --- Helpers ---

    private ProctoringSession getSessionOrThrow(UUID sessionId) {
        return sessionRepository.findById(sessionId)
                .orElseThrow(() -> new RuntimeException("Session not found: " + sessionId));
    }

    private int calculateScoreIncrement(Double confidenceScore) {
        // Scale confidence (0.0–1.0) to score increment (1–20)
        return (int) Math.round(confidenceScore * 20);
    }

    private ProctoringSessionResponse toSessionResponse(ProctoringSession s) {
        return ProctoringSessionResponse.builder()
                .id(s.getId())
                .studentId(s.getStudentId())
                .examId(s.getExamId())
                .attemptId(s.getAttemptId())
                .status(s.getStatus())
                .fraudScore(s.getFraudScore())
                .deviceFingerprint(s.getDeviceFingerprint())
                .startedAt(s.getStartedAt())
                .endedAt(s.getEndedAt())
                .build();
    }

    private FraudEventResponse toFraudEventResponse(FraudEvent e) {
        return FraudEventResponse.builder()
                .id(e.getId())
                .sessionId(e.getSessionId())
                .studentId(e.getStudentId())
                .examId(e.getExamId())
                .eventType(e.getEventType())
                .confidenceScore(e.getConfidenceScore())
                .details(e.getDetails())
                .detectedAt(e.getDetectedAt())
                .build();
    }
}