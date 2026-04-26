package net.ilyasse.assessmentservice.repository;


import net.ilyasse.assessmentservice.entity.ExamAttempt;
import net.ilyasse.assessmentservice.enums.AttemptStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/
public interface ExamAttemptRepository extends JpaRepository<ExamAttempt, UUID> {
    List<ExamAttempt> findByExamId(UUID examId);
    List<ExamAttempt> findByStudentId(UUID studentId);
    Optional<ExamAttempt> findByExamIdAndStudentId(UUID examId, UUID studentId);
    List<ExamAttempt> findByStatus(AttemptStatus status);
    List<ExamAttempt> findByExamIdAndStatus(UUID examId, AttemptStatus status);

}
