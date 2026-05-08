package net.ilyasse.assessmentservice.repository;

import net.ilyasse.assessmentservice.entity.QuestionRevision;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/
public interface QuestionRevisionRepository extends JpaRepository<QuestionRevision, UUID> {
    List<QuestionRevision> findByQuestionIdOrderByChangedAtDesc(UUID questionId);
}
