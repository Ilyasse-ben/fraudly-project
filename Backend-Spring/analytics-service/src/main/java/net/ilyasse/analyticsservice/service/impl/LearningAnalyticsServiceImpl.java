package net.ilyasse.analyticsservice.service.impl;

import jakarta.transaction.Transactional;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.ilyasse.analyticsservice.entity.StudentLearningProfile;
import net.ilyasse.analyticsservice.entity.TopicFrequency;
import net.ilyasse.analyticsservice.entity.TutorInteraction;
import net.ilyasse.analyticsservice.repository.StudentLearningProfileRepository;
import net.ilyasse.analyticsservice.repository.TopicFrequencyRepository;
import net.ilyasse.analyticsservice.repository.TutorInteractionRepository;
import net.ilyasse.analyticsservice.service.LearningAnalyticsService;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class LearningAnalyticsServiceImpl implements LearningAnalyticsService {
    private final TutorInteractionRepository tutorInteractionRepository;
    private final TopicFrequencyRepository topicFrequencyRepository;
    private final StudentLearningProfileRepository studentLearningProfileRepository;
    private final ObjectMapper objectMapper;

    @Override
    public void recordTutorInteraction(
            UUID studentId, UUID courseId, UUID chapterId,
            String sessionId, String question, String topic,
            String provider, Boolean fallbackUsed, Integer chunksUsed) {

        String normalizedTopic = normalizeTopic(topic);

        TutorInteraction interaction = TutorInteraction.builder()
                .studentId(studentId)
                .courseId(courseId)
                .chapterId(chapterId)
                .sessionId(sessionId)
                .question(question)
                .topic(normalizedTopic)
                .provider(provider)
                .fallbackUsed(fallbackUsed)
                .chunksUsed(chunksUsed)
                .build();

        tutorInteractionRepository.save(interaction);

        if (courseId != null) {
            syncStudentProfile(studentId, courseId);
        }

        log.info("[Analytics] Interaction enregistrée: student={} course={} topic={}",
                studentId, courseId, normalizedTopic);
    }

    @Override
    public void updateTopicFrequency(UUID studentId, UUID courseId, String topic) {
        Optional<TopicFrequency> existing = topicFrequencyRepository
                .findByStudentIdAndCourseIdAndTopic(studentId, courseId, topic);

        if (existing.isPresent()) {
            TopicFrequency tf = existing.get();
            tf.setCount(tf.getCount() + 1);
            tf.setLastAskedAt(LocalDateTime.now());
            topicFrequencyRepository.save(tf);
        } else {
            TopicFrequency tf = TopicFrequency.builder()
                    .studentId(studentId)
                    .courseId(courseId)
                    .topic(topic)
                    .count(1)
                    .lastAskedAt(LocalDateTime.now())
                    .build();
            topicFrequencyRepository.save(tf);
        }
    }

    @Override
    public List<String> getWeakTopics(UUID studentId, UUID courseId, int minCount) {
        return topicFrequencyRepository
                .findWeakTopics(studentId, courseId, minCount)
                .stream()
                .map(TopicFrequency::getTopic)
                .collect(Collectors.toList());
    }

    @Override
    public List<Map<String, Object>> getCourseTopicStats(UUID courseId) {
        List<Object[]> stats = topicFrequencyRepository.findTopicStatsByCourse(courseId);
        List<Map<String, Object>> result = new ArrayList<>();

        for (Object[] row : stats) {
            Map<String, Object> item = new HashMap<>();
            item.put("topic", row[0]);
            item.put("totalQuestions", row[1]);
            result.add(item);
        }
        return result;
    }

    @Override
    public Map<String, Object> getStudentProfile(UUID studentId, UUID courseId) {
        Optional<StudentLearningProfile> profileOpt = courseId != null
                ? studentLearningProfileRepository.findByStudentIdAndCourseId(studentId, courseId)
                : studentLearningProfileRepository.findTopByStudentIdOrderByUpdatedAtDesc(studentId);

        StudentLearningProfile profile = profileOpt.orElse(null);

        UUID resolvedCourseId = profile != null ? profile.getCourseId() : courseId;
        List<String> completedChapters = profile != null
                ? readStringList(profile.getCompletedChaptersJson())
                : Collections.emptyList();
        Map<String, Double> scores = profile != null
                ? readScoreMap(profile.getScoresJson())
                : Collections.emptyMap();
        List<String> weakTopics = profile != null
                ? readStringList(profile.getWeakTopicsJson())
                : (resolvedCourseId != null ? getWeakTopics(studentId, resolvedCourseId, 3) : Collections.emptyList());
        Integer interactionsCount = profile != null ? profile.getInteractionsCount() : 0;

        Map<String, Object> payload = new HashMap<>();
        payload.put("student_id", studentId);
        payload.put("course_id", resolvedCourseId);
        payload.put("completed_chapters", completedChapters);
        payload.put("scores", scores);
        payload.put("weak_topics", weakTopics);
        payload.put("interactions_count", interactionsCount);
        payload.put(
            "last_interaction_at",
            (profile != null && profile.getLastInteractionAt() != null)
                ? profile.getLastInteractionAt().toString()
                : null
        );
        return payload;
    }

    private void syncStudentProfile(UUID studentId, UUID courseId) {
        StudentLearningProfile profile = studentLearningProfileRepository
                .findByStudentIdAndCourseId(studentId, courseId)
                .orElseGet(() -> StudentLearningProfile.builder()
                        .studentId(studentId)
                        .courseId(courseId)
                        .completedChaptersJson("[]")
                        .scoresJson("{}")
                        .weakTopicsJson("[]")
                        .interactionsCount(0)
                        .build());

        profile.setInteractionsCount((profile.getInteractionsCount() == null ? 0 : profile.getInteractionsCount()) + 1);
        profile.setLastInteractionAt(LocalDateTime.now());
        profile.setWeakTopicsJson(writeAsJson(getWeakTopics(studentId, courseId, 3)));
        if (profile.getCompletedChaptersJson() == null || profile.getCompletedChaptersJson().isBlank()) {
            profile.setCompletedChaptersJson("[]");
        }
        if (profile.getScoresJson() == null || profile.getScoresJson().isBlank()) {
            profile.setScoresJson("{}");
        }

        studentLearningProfileRepository.save(profile);
    }

    private String normalizeTopic(String topic) {
        if (topic == null || topic.isBlank()) {
            return "général";
        }
        return topic.trim().toLowerCase(Locale.ROOT);
    }

    private List<String> readStringList(String json) {
        try {
            if (json == null || json.isBlank()) {
                return Collections.emptyList();
            }
            return objectMapper.readValue(json, new TypeReference<List<String>>() {});
        } catch (Exception e) {
            return Collections.emptyList();
        }
    }

    private Map<String, Double> readScoreMap(String json) {
        try {
            if (json == null || json.isBlank()) {
                return Collections.emptyMap();
            }
            return objectMapper.readValue(json, new TypeReference<Map<String, Double>>() {});
        } catch (Exception e) {
            return Collections.emptyMap();
        }
    }

    private String writeAsJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (Exception e) {
            return "[]";
        }
    }
}
