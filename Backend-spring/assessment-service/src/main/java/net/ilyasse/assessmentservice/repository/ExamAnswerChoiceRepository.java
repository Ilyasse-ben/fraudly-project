package net.ilyasse.assessmentservice.repository;

import net.ilyasse.assessmentservice.entity.ExamAnswerChoice;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;
/**
 * @author ELHAID Yousef
 **/
public interface ExamAnswerChoiceRepository extends JpaRepository<ExamAnswerChoice, UUID> {
    List<ExamAnswerChoice> findByAnswerId(UUID answerId);
    void deleteByAnswerId(UUID answerId);
}
