package net.ilyasse.analyticsservice.repository;

import net.ilyasse.analyticsservice.entity.StudentLearningProfile;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface StudentLearningProfileRepository extends JpaRepository<StudentLearningProfile, UUID> {
    Optional<StudentLearningProfile> findByStudentIdAndCourseId(UUID studentId, UUID courseId);
    Optional<StudentLearningProfile> findTopByStudentIdOrderByUpdatedAtDesc(UUID studentId);
}
