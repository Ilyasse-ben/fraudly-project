package net.ilyasse.analyticsservice.repository;

import net.ilyasse.analyticsservice.entity.TutorInteraction;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface TutorInteractionRepository extends JpaRepository<TutorInteraction, UUID> {
    List<TutorInteraction> findByStudentIdAndCourseId(UUID studentId, UUID courseId);
    List<TutorInteraction> findByStudentId(UUID studentId);
    List<TutorInteraction> findByCourseId(UUID courseId);
}
