package net.ilyasse.assessmentservice.repository;


import net.ilyasse.assessmentservice.entity.Exam;
import net.ilyasse.assessmentservice.enums.ExamStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
/**
 * @author ELHAID Yousef
 **/
public interface ExamRepository extends JpaRepository<Exam, Long> {
    List<Exam> findByCourseId(Long courseId);
    List<Exam> findByProfessorId(Long professorId);
    List<Exam> findByStatus(ExamStatus status);
}
