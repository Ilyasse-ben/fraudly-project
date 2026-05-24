package net.ilyasse.analyticsservice.service;

import java.util.List;
import java.util.Map;
import java.util.UUID;

public interface LearningAnalyticsService {
    void recordTutorInteraction(
            UUID studentId, UUID courseId, UUID chapterId,
            String sessionId, String question, String topic,
            String provider, Boolean fallbackUsed, Integer chunksUsed
    );
    void updateTopicFrequency(UUID studentId, UUID courseId, String topic);
    List<String> getWeakTopics(UUID studentId, UUID courseId, int minCount);
    List<Map<String, Object>> getCourseTopicStats(UUID courseId);
    Map<String, Object> getStudentProfile(UUID studentId, UUID courseId);
}
