package net.fruadly.learningservice.kafka;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.fruadly.learningservice.dto.AiResultEvent;
import net.fruadly.learningservice.service.ResourceIngestionStatusService;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class AiResultListener {

    private final ObjectMapper objectMapper;
    private final ResourceIngestionStatusService resourceIngestionStatusService;

    @KafkaListener(topics = "${KAFKA_TOPIC_AI_RESULTS:ai_results}", groupId = "${spring.kafka.consumer.group-id}")
    public void onAiResult(String message) {
        try {
            log.info("AI EVENT RAW = {}", message);
            AiResultEvent event = objectMapper.readValue(message, AiResultEvent.class);
            resourceIngestionStatusService.applyAiResult(event, message);
        } catch (JsonProcessingException e) {
            // Malformed payload should be logged and skipped to keep consumer healthy.
            log.error("Invalid ai_results payload, skipping message: {}", message, e);
        }
    }
}
