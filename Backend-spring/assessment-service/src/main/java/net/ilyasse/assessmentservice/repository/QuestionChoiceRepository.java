package net.ilyasse.assessmentservice.repository;

import net.ilyasse.assessmentservice.entity.QuestionChoice;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/
public interface QuestionChoiceRepository extends JpaRepository<QuestionChoice, UUID> {
    List<QuestionChoice> findByQuestionId(UUID questionId);
    void deleteByQuestionId(UUID questionId);
}
