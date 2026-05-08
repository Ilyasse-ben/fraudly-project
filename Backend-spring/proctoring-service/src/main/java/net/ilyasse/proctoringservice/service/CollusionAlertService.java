package net.ilyasse.proctoringservice.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import net.ilyasse.proctoringservice.dto.CollusionAlertResponse;
import net.ilyasse.proctoringservice.dto.CollusionPairResponse;
import net.ilyasse.proctoringservice.entity.CollusionAlert;
import net.ilyasse.proctoringservice.entity.CollusionPair;
import net.ilyasse.proctoringservice.repository.CollusionAlertRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Transactional
public class CollusionAlertService {

    private final CollusionAlertRepository collusionAlertRepository;
    private final ObjectMapper objectMapper;

    public void persistCollusionEvent(Map<String, Object> event) {
        UUID examId = toUUID(event.get("exam_id"));
        if (examId == null) {
            return;
        }

        UUID courseId = toUUID(event.get("course_id"));
        LocalDateTime detectedAt = parseDate(event.get("detected_at"));
        List<Map<String, Object>> pairs = asMapList(event.get("suspected_pairs"));

        CollusionAlert alert = CollusionAlert.builder()
                .examId(examId)
                .courseId(courseId)
                .detectedAt(detectedAt != null ? detectedAt : LocalDateTime.now())
                .pairCount(pairs.size())
                .rawEvent(asJson(event))
                .suspectedPairs(new ArrayList<>())
                .build();

        for (Map<String, Object> p : pairs) {
            CollusionPair pair = CollusionPair.builder()
                    .alert(alert)
                    .questionId(toUUID(p.get("question_id")))
                    .studentAId(toUUID(p.get("student_a_id")))
                    .studentBId(toUUID(p.get("student_b_id")))
                    .studentAName(toStringOrNull(p.get("student_a_name")))
                    .studentBName(toStringOrNull(p.get("student_b_name")))
                    .similarityScore(toDouble(p.get("similarity_score")))
                    .answerAPreview(toStringOrNull(p.get("answer_a_preview")))
                    .answerBPreview(toStringOrNull(p.get("answer_b_preview")))
                    .build();
            alert.getSuspectedPairs().add(pair);
        }

        collusionAlertRepository.save(alert);
    }

    @Transactional(readOnly = true)
    public List<CollusionAlertResponse> getAll() {
        return collusionAlertRepository.findAll()
                .stream()
                .map(this::toResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public List<CollusionAlertResponse> getByExamId(UUID examId) {
        return collusionAlertRepository.findByExamIdOrderByDetectedAtDesc(examId)
                .stream()
                .map(this::toResponse)
                .toList();
    }

    private CollusionAlertResponse toResponse(CollusionAlert alert) {
        return CollusionAlertResponse.builder()
                .id(alert.getId())
                .examId(alert.getExamId())
                .courseId(alert.getCourseId())
                .detectedAt(alert.getDetectedAt())
                .pairCount(alert.getPairCount())
                .createdAt(alert.getCreatedAt())
                .suspectedPairs(alert.getSuspectedPairs().stream().map(p -> CollusionPairResponse.builder()
                        .id(p.getId())
                        .questionId(p.getQuestionId())
                        .studentAId(p.getStudentAId())
                        .studentBId(p.getStudentBId())
                        .studentAName(p.getStudentAName())
                        .studentBName(p.getStudentBName())
                        .similarityScore(p.getSimilarityScore())
                        .answerAPreview(p.getAnswerAPreview())
                        .answerBPreview(p.getAnswerBPreview())
                        .build()).toList())
                .build();
    }

    private UUID toUUID(Object value) {
        if (value == null) {
            return null;
        }
        try {
            return UUID.fromString(value.toString());
        } catch (Exception e) {
            return null;
        }
    }

    private LocalDateTime parseDate(Object value) {
        if (value == null) {
            return null;
        }
        try {
            return OffsetDateTime.parse(value.toString()).toLocalDateTime();
        } catch (Exception e) {
            return null;
        }
    }

    private List<Map<String, Object>> asMapList(Object value) {
        if (value instanceof List<?> list) {
            List<Map<String, Object>> result = new ArrayList<>();
            for (Object item : list) {
                if (item instanceof Map<?, ?> rawMap) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> casted = (Map<String, Object>) rawMap;
                    result.add(casted);
                }
            }
            return result;
        }
        return List.of();
    }

    private Double toDouble(Object value) {
        if (value == null) {
            return 0.0;
        }
        try {
            return Double.parseDouble(value.toString());
        } catch (Exception e) {
            return 0.0;
        }
    }

    private String toStringOrNull(Object value) {
        return value != null ? value.toString() : null;
    }

    private String asJson(Map<String, Object> event) {
        try {
            return objectMapper.writeValueAsString(event);
        } catch (JsonProcessingException e) {
            return "{}";
        }
    }
}
