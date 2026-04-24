package net.ilyasse.assessmentservice.repository;


import net.ilyasse.assessmentservice.entity.ExamAttempt;
import net.ilyasse.assessmentservice.enums.AttemptStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

/**
 * @author ELHAID Yousef
 **/
public interface ExamAttemptRepository extends JpaRepository<ExamAttempt, Long> {
    List<ExamAttempt> findByExamId(Long examId);
    List<ExamAttempt> findByStudentId(Long studentId);
    Optional<ExamAttempt> findByExamIdAndStudentId(Long examId, Long studentId);
    List<ExamAttempt> findByStatus(AttemptStatus status);
}
