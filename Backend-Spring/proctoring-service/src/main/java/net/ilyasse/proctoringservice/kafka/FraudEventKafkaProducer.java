package net.ilyasse.proctoringservice.kafka;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.ilyasse.proctoringservice.entity.FraudEvent;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class FraudEventKafkaProducer {

    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;

    @Value("${kafka.topic.fraud.events}")
    private String fraudEventsTopic;

    @Value("${kafka.topic.fraud.flagged}")
    private String fraudFlaggedTopic;

    public void publishFraudEvent(FraudEvent event) {
        try {
            Map<String, Object> payload = Map.of(
                    "session_id", event.getSessionId().toString(),
                    "student_id", event.getStudentId().toString(),
                    "exam_id", event.getExamId().toString(),
                    "event_type", event.getEventType().name(),
                    "confidence_score", event.getConfidenceScore(),
                    "details", event.getDetails() != null ? event.getDetails() : "",
                    "detected_at", event.getDetectedAt().toString()
            );
            String message = objectMapper.writeValueAsString(payload);
            kafkaTemplate.send(fraudEventsTopic, event.getSessionId().toString(), message);
            log.info("[FraudEvent] Published event={} session={}", event.getEventType(), event.getSessionId());
        } catch (Exception e) {
            log.error("[FraudEvent] Failed to publish event: {}", e.getMessage());
        }
    }

    public void publishSessionFlagged(FraudEvent triggeringEvent, int fraudScore) {
        try {
            Map<String, Object> payload = Map.of(
                    "session_id", triggeringEvent.getSessionId().toString(),
                    "student_id", triggeringEvent.getStudentId().toString(),
                    "exam_id", triggeringEvent.getExamId().toString(),
                    "fraud_score", fraudScore,
                    "triggered_by", triggeringEvent.getEventType().name(),
                    "flagged_at", triggeringEvent.getDetectedAt().toString()
            );
            String message = objectMapper.writeValueAsString(payload);
            kafkaTemplate.send(fraudFlaggedTopic, triggeringEvent.getSessionId().toString(), message);
            log.warn("[FraudEvent] Session FLAGGED session={} score={}", triggeringEvent.getSessionId(), fraudScore);
        } catch (Exception e) {
            log.error("[FraudEvent] Failed to publish flagged event: {}", e.getMessage());
        }
    }
}