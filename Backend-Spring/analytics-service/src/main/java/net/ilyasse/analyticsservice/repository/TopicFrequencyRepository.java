package net.ilyasse.analyticsservice.repository;

import net.ilyasse.analyticsservice.entity.TopicFrequency;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface TopicFrequencyRepository extends JpaRepository<TopicFrequency, UUID> {

    Optional<TopicFrequency> findByStudentIdAndCourseIdAndTopic(
            UUID studentId, UUID courseId, String topic
    );

    List<TopicFrequency> findByStudentIdAndCourseIdOrderByCountDesc(
            UUID studentId, UUID courseId
    );

    @Query("SELECT t FROM TopicFrequency t WHERE t.studentId = :studentId " +
            "AND t.courseId = :courseId AND t.count >= :minCount " +
            "ORDER BY t.count DESC")
    List<TopicFrequency> findWeakTopics(
            @Param("studentId") UUID studentId,
            @Param("courseId") UUID courseId,
            @Param("minCount") int minCount
    );

    @Query("SELECT t.topic, SUM(t.count) as total FROM TopicFrequency t " +
            "WHERE t.courseId = :courseId GROUP BY t.topic ORDER BY total DESC")
    List<Object[]> findTopicStatsByCourse(@Param("courseId") UUID courseId);
}