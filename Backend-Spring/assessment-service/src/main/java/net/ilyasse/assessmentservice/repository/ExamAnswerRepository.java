package net.ilyasse.assessmentservice.repository;


import net.ilyasse.assessmentservice.entity.ExamAnswer;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
/**
 * @author ELHAID Yousef
 **/
public interface ExamAnswerRepository extends JpaRepository<ExamAnswer, Long> {
    List<ExamAnswer> findByAttemptId(Long attemptId);
    List<ExamAnswer> findByAttemptIdAndIsGraded(Long attemptId, Boolean isGraded);
}
