package net.ilyasse.assessmentservice.repository;

import net.ilyasse.assessmentservice.entity.ExamAnswerChoice;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
/**
 * @author ELHAID Yousef
 **/
public interface ExamAnswerChoiceRepository extends JpaRepository<ExamAnswerChoice, Long> {
    List<ExamAnswerChoice> findByAnswerId(Long answerId);
    void deleteByAnswerId(Long answerId);
}
