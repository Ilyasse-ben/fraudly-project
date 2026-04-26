package net.ilyasse.assessmentservice.kafka;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.ilyasse.assessmentservice.entity.ExamAnswer;
import net.ilyasse.assessmentservice.entity.ExamAttempt;
import net.ilyasse.assessmentservice.enums.AttemptStatus;
import net.ilyasse.assessmentservice.repository.*;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.UUID;

@Slf4j
@Component
@RequiredArgsConstructor
public class ExamScoredKafkaConsumer {

    private final ExamAnswerRepository examAnswerRepository;
    private final ExamAttemptRepository examAttemptRepository;
    private final ExamQuestionRepository examQuestionRepository;
    private final ObjectMapper objectMapper;

    @KafkaListener(
        topics = "${kafka.topic.exam.scored}",
        groupId = "${spring.kafka.consumer.group-id}"
    )
    public void consumeExamScored(String message) {
        try {
            Map<String, Object> event = objectMapper.readValue(message, Map.class);

            UUID questionId = UUID.fromString(event.get("question_id").toString());
            UUID studentId = UUID.fromString(event.get("student_id").toString());
            UUID examId = UUID.fromString(event.get("exam_id").toString());
            double score = Double.parseDouble(event.get("score").toString());
            String feedback = event.get("feedback").toString();

            // Recherche de la tentative de l'etudiant
            ExamAttempt attempt = examAttemptRepository
                .findByExamIdAndStudentId(examId, studentId)
                .orElseThrow(() -> new RuntimeException(
                    "Attempt not found: exam=" + examId + " student=" + studentId));

            // Mis à jour ExamAnswer
            examAnswerRepository
                .findByAttemptIdAndQuestionId(attempt.getId(), questionId)
                .ifPresent(answer -> {
                    answer.setPointsAwarded(score);
                    answer.setIsGraded(true);
                    answer.setAnswerText(answer.getAnswerText() + "\n[Feedback: " + feedback + "]");
                    examAnswerRepository.save(answer);
                    log.info("[Scorer] Answer updated: question={} student={} score={}", 
                        questionId, studentId, score);
                });

            // Recalculation du score total
            recalculateAttemptScore(attempt);

        } catch (Exception e) {
            log.error("[Scorer] Erreur consommation: {}", e.getMessage());
        }
    }

    @KafkaListener(
        topics = "${kafka.topic.collusion.suspected}",
        groupId = "${spring.kafka.consumer.group-id}"
    )
    public void consumeCollusionSuspected(String message) {
        try {
            Map<String, Object> event = objectMapper.readValue(message, Map.class);
            log.warn("[Collusion] Alerte reçue: exam={} pairs={}", 
                event.get("exam_id"), event.get("suspected_pairs"));
            // TODO: stocker en DB + notifier prof
        } catch (Exception e) {
            log.error("[Collusion] Erreur consommation: {}", e.getMessage());
        }
    }

    private void recalculateAttemptScore(ExamAttempt attempt) {
        double totalScore = examAnswerRepository
            .findByAttemptId(attempt.getId())
            .stream()
            .mapToDouble(a -> a.getPointsAwarded() != null ? a.getPointsAwarded() : 0.0)
            .sum();

        attempt.setScore(totalScore);
        attempt.setStatus(AttemptStatus.GRADED);
        examAttemptRepository.save(attempt);
        log.info("[Score] Attempt recalculé: id={} score={}", attempt.getId(), totalScore);
    }
}