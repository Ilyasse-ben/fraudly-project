package net.ilyasse.assessmentservice.repository;


import net.ilyasse.assessmentservice.entity.Exam;
import net.ilyasse.assessmentservice.enums.ExamStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;
/**
 * @author ELHAID Yousef
 **/
public interface ExamRepository extends JpaRepository<Exam, UUID> {
    List<Exam> findByCourseId(UUID courseId);
    List<Exam> findByProfessorId(UUID professorId);
    List<Exam> findByStatus(ExamStatus status);
}
