package net.ilyasse.analyticsservice.kafka;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.ilyasse.analyticsservice.service.LearningAnalyticsService;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.UUID;

@Slf4j
@Component
@RequiredArgsConstructor
public class TutorInteractionConsumer {
    private final LearningAnalyticsService learningAnalyticsService;
    private final ObjectMapper objectMapper;

    @KafkaListener(
            topics = "${kafka.topic.tutor.interaction}",
            groupId = "${spring.kafka.consumer.group-id}"
    )
    public void consume(String message) {
        try {
            Map<String, Object> event = objectMapper.readValue(message, Map.class);

            UUID studentId = UUID.fromString(event.get("student_id").toString());
            UUID courseId = event.get("course_id") != null ?
                    UUID.fromString(event.get("course_id").toString()) : null;
            UUID chapterId = event.get("chapter_id") != null ?
                    UUID.fromString(event.get("chapter_id").toString()) : null;
            String sessionId = event.get("session_id").toString();
            String question = event.get("question").toString();
            String topic = event.get("topic") != null ?
                    event.get("topic").toString() : "général";
            String provider = event.get("provider") != null ?
                    event.get("provider").toString() : "unknown";
            Boolean fallbackUsed = event.get("fallback_used") != null &&
                    Boolean.parseBoolean(event.get("fallback_used").toString());
            Integer chunksUsed = event.get("chunks_used") != null ?
                    Integer.parseInt(event.get("chunks_used").toString()) : 0;

            if (courseId != null) {
                learningAnalyticsService.updateTopicFrequency(studentId, courseId, topic);
            }

            // Enregistrer l'interaction
            learningAnalyticsService.recordTutorInteraction(
                    studentId, courseId, chapterId,
                    sessionId, question, topic,
                    provider, fallbackUsed, chunksUsed
            );

            log.info("[TutorConsumer] Interaction traitée: student={} topic={}", studentId, topic);

        } catch (Exception e) {
            log.error("[TutorConsumer] Erreur traitement: {}", e.getMessage());
        }
    }
}
