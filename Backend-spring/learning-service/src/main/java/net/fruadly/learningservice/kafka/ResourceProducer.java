package net.fruadly.learningservice.kafka;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.fruadly.learningservice.dto.ResourceDto;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class ResourceProducer {

    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${KAFKA_TOPIC_RESOURCE_UPLOADED:resource_uploaded}")
    private String resourceTopic;

    public void publishResource(ResourceDto resource, byte[] fileBytes, String courseId, String chapterId) {
        try {
            Map<String, Object> event = new HashMap<>();
            event.put("resource_id", resource.getId().toString());
            event.put("course_id", courseId);
            event.put("chapter_id", chapterId);
            event.put("filename", resource.getFileName());
            event.put("content_type", resource.getMimeType());
            event.put("file_content_base64", Base64.getEncoder().encodeToString(fileBytes));

            String payload = objectMapper.writeValueAsString(event);
            kafkaTemplate.send(resourceTopic, payload);
            log.info("Published resource_uploaded for {} to topic {}", resource.getId(), resourceTopic);
        } catch (Exception e) {
            log.error("Failed publishing resource_uploaded", e);
        }
    }
}
