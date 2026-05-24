package net.ilyasse.assessmentservice.repository;


import net.ilyasse.assessmentservice.entity.ExamQuestion;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;
/**
 * @author ELHAID Yousef
 **/
public interface ExamQuestionRepository extends JpaRepository<ExamQuestion, UUID> {
    List<ExamQuestion> findByExamIdOrderByOrderIndex(UUID examId);
    void deleteByExamId(UUID examId);
}