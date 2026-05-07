package net.fruadly.learningservice.kafka;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class LearningPathListener {

    @Value("${KAFKA_TOPIC_LEARNING_PATH_UPDATE:learning_path_update}")
    private String learningPathTopic;

    @KafkaListener(topics = "${KAFKA_TOPIC_LEARNING_PATH_UPDATE:learning_path_update}", groupId = "${spring.kafka.consumer.group-id}")
    public void onLearningPathUpdate(String message) {
        log.info("Received learning_path_update: {}", message);
    }
}
