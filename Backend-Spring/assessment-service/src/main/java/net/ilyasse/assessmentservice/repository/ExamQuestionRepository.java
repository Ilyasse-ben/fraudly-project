package net.ilyasse.assessmentservice.repository;


import net.ilyasse.assessmentservice.entity.ExamQuestion;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
/**
 * @author ELHAID Yousef
 **/
public interface ExamQuestionRepository extends JpaRepository<ExamQuestion, Long> {
    List<ExamQuestion> findByExamIdOrderByOrderIndex(Long examId);
    void deleteByExamId(Long examId);
}