package net.ilyasse.assessmentservice.kafka;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.ilyasse.assessmentservice.entity.*;
import net.ilyasse.assessmentservice.enums.AttemptStatus;
import net.ilyasse.assessmentservice.enums.QuestionType;
import net.ilyasse.assessmentservice.repository.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.*;
import java.util.UUID;

@Slf4j
@Component
@RequiredArgsConstructor
public class CorrectionKafkaProducer {

    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;
    private final ExamAttemptRepository examAttemptRepository;
    private final ExamAnswerRepository examAnswerRepository;
    private final ExamQuestionRepository examQuestionRepository;

    @Value("${kafka.topic.exam.correction.requested}")
    private String correctionTopic;

    public void publishCorrectionRequested(UUID examId, UUID professorId) {
        try {
            // Récupération de toutes les soumissions
            List<ExamAttempt> attempts = examAttemptRepository
                .findByExamIdAndStatus(examId, AttemptStatus.SUBMITTED);

            List<Map<String, Object>> submissions = new ArrayList<>();

            for (ExamAttempt attempt : attempts) {
                // Récupération des questions ouvertes
                List<ExamAnswer> openAnswers = examAnswerRepository
                    .findByAttemptIdAndQuestionType(attempt.getId(), QuestionType.OPEN);

                if (openAnswers.isEmpty()) continue;

                List<Map<String, Object>> answers = new ArrayList<>();
                for (ExamAnswer answer : openAnswers) {
                    ExamQuestion question = answer.getQuestion();
                    Map<String, Object> answerMap = new HashMap<>();
                    answerMap.put("question_id", question.getId().toString());
                    answerMap.put("student_answer", answer.getAnswerText());
                    answerMap.put("correct_answer", question.getCorrectAnswer());
                    answerMap.put("explanation", question.getExplanation());
                    answerMap.put("max_score", question.getPoints());
                    answers.add(answerMap);
                }

                Map<String, Object> submission = new HashMap<>();
                submission.put("student_id", attempt.getStudentId().toString());
                submission.put("open_answers", answers);
                submissions.add(submission);
            }

            // construction de l'évenement
            Map<String, Object> event = new HashMap<>();
            event.put("exam_id", examId.toString());
            event.put("requested_at", LocalDateTime.now().toString());
            event.put("submissions", submissions);

            String message = objectMapper.writeValueAsString(event);
            kafkaTemplate.send(correctionTopic, examId.toString(), message);

            log.info("[Correction] Publié exam_id={} submissions={}", 
                examId, submissions.size());

        } catch (Exception e) {
            log.error("[Correction] Erreur publication: {}", e.getMessage());
            throw new RuntimeException("Failed to publish correction event", e);
        }
    }
}