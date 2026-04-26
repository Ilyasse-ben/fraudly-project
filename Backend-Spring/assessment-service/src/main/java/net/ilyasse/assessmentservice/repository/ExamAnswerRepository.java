package net.ilyasse.assessmentservice.repository;
import net.ilyasse.assessmentservice.enums.QuestionType;

import net.ilyasse.assessmentservice.entity.ExamAnswer;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;
import java.util.UUID;
/**
 * @author ELHAID Yousef
 **/
public interface ExamAnswerRepository extends JpaRepository<ExamAnswer, UUID> {
    List<ExamAnswer> findByAttemptId(UUID attemptId);
    List<ExamAnswer> findByAttemptIdAndIsGraded(UUID attemptId, Boolean isGraded);

    @Query("SELECT a FROM ExamAnswer a WHERE a.attempt.id = :attemptId AND a.question.type = :type")
    List<ExamAnswer> findByAttemptIdAndQuestionType(
            @Param("attemptId") UUID attemptId,
            @Param("type") QuestionType type
    );
        Optional<ExamAnswer> findByAttemptIdAndQuestionId(UUID attemptId, UUID questionId);
}
