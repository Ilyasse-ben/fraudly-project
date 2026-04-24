package net.ilyasse.assessmentservice.repository;

import net.ilyasse.assessmentservice.entity.QuestionRevision;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

/**
 * @author ELHAID Yousef
 **/
public interface QuestionRevisionRepository extends JpaRepository<QuestionRevision, Long> {
    List<QuestionRevision> findByQuestionIdOrderByChangedAtDesc(Long questionId);
}
