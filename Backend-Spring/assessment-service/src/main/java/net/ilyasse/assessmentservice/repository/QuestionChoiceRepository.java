package net.ilyasse.assessmentservice.repository;

import net.ilyasse.assessmentservice.entity.QuestionChoice;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

/**
 * @author ELHAID Yousef
 **/
public interface QuestionChoiceRepository extends JpaRepository<QuestionChoice, Long> {
    List<QuestionChoice> findByQuestionId(Long questionId);
    void deleteByQuestionId(Long questionId);
}
