package net.ilyasse.proctoringservice.kafka;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.ilyasse.proctoringservice.service.CollusionAlertService;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class CollusionKafkaConsumer {

    private final ObjectMapper objectMapper;
    private final CollusionAlertService collusionAlertService;

    @KafkaListener(
            topics = "${kafka.topic.collusion.suspected}",
            groupId = "${spring.kafka.consumer.group-id}"
    )
    public void consumeCollusionSuspected(String message) {
        try {
            Map<String, Object> event = objectMapper.readValue(message, Map.class);
            collusionAlertService.persistCollusionEvent(event);
            log.info("[Collusion] Alerte persistee exam={} pairs={}",
                    event.get("exam_id"),
                    event.get("suspected_pairs"));
        } catch (Exception e) {
            log.error("[Collusion] Erreur persistance alerte: {}", e.getMessage());
        }
    }
}
