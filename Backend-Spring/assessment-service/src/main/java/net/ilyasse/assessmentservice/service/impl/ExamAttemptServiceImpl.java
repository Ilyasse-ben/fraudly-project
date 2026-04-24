package net.ilyasse.assessmentservice.service.impl;

import lombok.RequiredArgsConstructor;
import net.ilyasse.assessmentservice.dto.request.StartAttemptRequest;
import net.ilyasse.assessmentservice.dto.request.SubmitAnswerRequest;
import net.ilyasse.assessmentservice.dto.request.SubmitAttemptRequest;
import net.ilyasse.assessmentservice.dto.response.ExamAttemptResponse;
import net.ilyasse.assessmentservice.entity.*;
import net.ilyasse.assessmentservice.enums.AttemptStatus;
import net.ilyasse.assessmentservice.enums.QuestionType;
import net.ilyasse.assessmentservice.repository.*;
import net.ilyasse.assessmentservice.service.ExamAttemptService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

/**
 * @author ELHAID Yousef
 **/
@Service
@RequiredArgsConstructor
@Transactional
public class ExamAttemptServiceImpl implements ExamAttemptService {

    private final ExamAttemptRepository examAttemptRepository;
    private final ExamAnswerRepository examAnswerRepository;
    private final ExamAnswerChoiceRepository examAnswerChoiceRepository;
    private final ExamRepository examRepository;
    private final ExamQuestionRepository examQuestionRepository;
    private final QuestionChoiceRepository questionChoiceRepository;

    @Override
    public ExamAttemptResponse startAttempt(StartAttemptRequest request) {
        // Check if student already has an attempt
        examAttemptRepository.findByExamIdAndStudentId(
                        request.getExamId(), request.getStudentId())
                .ifPresent(a -> {
                    throw new RuntimeException("Student already has an attempt for this exam");
                });

        Exam exam = examRepository.findById(request.getExamId())
                .orElseThrow(() -> new RuntimeException("Exam not found"));

        ExamAttempt attempt = ExamAttempt.builder()
                .exam(exam)
                .studentId(request.getStudentId())
                .status(AttemptStatus.STARTED)
                .build();

        attempt = examAttemptRepository.save(attempt);
        return mapToResponse(attempt);
    }

    @Override
    public ExamAttemptResponse submitAttempt(SubmitAttemptRequest request) {
        ExamAttempt attempt = examAttemptRepository.findById(request.getAttemptId())
                .orElseThrow(() -> new RuntimeException("Attempt not found"));

        double totalScore = 0;
        double maxScore = 0;

        for (SubmitAnswerRequest answerReq : request.getAnswers()) {
            ExamQuestion question = examQuestionRepository.findById(answerReq.getQuestionId())
                    .orElseThrow(() -> new RuntimeException("Question not found"));

            maxScore += question.getPoints();

            ExamAnswer answer = ExamAnswer.builder()
                    .attempt(attempt)
                    .question(question)
                    .build();

            if (question.getType() == QuestionType.OPEN) {
                // Redaction → save text, not graded yet
                answer.setAnswerText(answerReq.getAnswerText());
                answer.setIsGraded(false);
                answer.setPointsAwarded(0.0);

            } else if (question.getType() == QuestionType.QCM_MULTIPLE) {
                // Multiple choices → save in ExamAnswerChoice
                answer.setIsGraded(true);
                answer = examAnswerRepository.save(answer);

                double points = 0;
                if (answerReq.getSelectedChoiceIds() != null) {
                    for (Long choiceId : answerReq.getSelectedChoiceIds()) {
                        ExamAnswerChoice answerChoice = ExamAnswerChoice.builder()
                                .answer(answer)
                                .choiceId(choiceId)
                                .build();
                        examAnswerChoiceRepository.save(answerChoice);

                        // Check if correct
                        questionChoiceRepository.findById(choiceId).ifPresent(c -> {
                            if (c.getIsCorrect()) {
                            }
                        });
                    }
                    // Simple scoring: all correct choices selected = full points
                    long correctSelected = answerReq.getSelectedChoiceIds().stream()
                            .filter(id -> questionChoiceRepository.findById(id)
                                    .map(QuestionChoice::getIsCorrect).orElse(false))
                            .count();
                    long totalCorrect = questionChoiceRepository.findByQuestionId(question.getId())
                            .stream().filter(QuestionChoice::getIsCorrect).count();
                    if (totalCorrect > 0 && correctSelected == totalCorrect) {
                        points = question.getPoints();
                    }
                }
                answer.setPointsAwarded(points);
                answer.setIsCorrect(points > 0);
                totalScore += points;
                examAnswerRepository.save(answer);
                continue;

            } else {
                // QCM_SINGLE or TRUE_FALSE
                answer.setSelectedChoiceId(answerReq.getSelectedChoiceId());
                answer.setIsGraded(true);

                boolean isCorrect = false;
                if (answerReq.getSelectedChoiceId() != null) {
                    isCorrect = questionChoiceRepository.findById(answerReq.getSelectedChoiceId())
                            .map(QuestionChoice::getIsCorrect).orElse(false);
                }
                answer.setIsCorrect(isCorrect);
                answer.setPointsAwarded(isCorrect ? question.getPoints() : 0.0);
                if (isCorrect) totalScore += question.getPoints();
            }

            examAnswerRepository.save(answer);
        }

        // Update attempt
        attempt.setStatus(AttemptStatus.SUBMITTED);
        attempt.setSubmittedAt(LocalDateTime.now());
        attempt.setScore(totalScore);
        attempt.setMaxScore(maxScore);
        attempt = examAttemptRepository.save(attempt);

        return mapToResponse(attempt);
    }

    @Override
    public ExamAttemptResponse getAttemptById(Long attemptId) {
        ExamAttempt attempt = examAttemptRepository.findById(attemptId)
                .orElseThrow(() -> new RuntimeException("Attempt not found"));
        return mapToResponse(attempt);
    }

    @Override
    public List<ExamAttemptResponse> getAttemptsByStudent(Long studentId) {
        return examAttemptRepository.findByStudentId(studentId)
                .stream().map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    @Override
    public List<ExamAttemptResponse> getAttemptsByExam(Long examId) {
        return examAttemptRepository.findByExamId(examId)
                .stream().map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    private ExamAttemptResponse mapToResponse(ExamAttempt attempt) {
        return ExamAttemptResponse.builder()
                .id(attempt.getId())
                .examId(attempt.getExam().getId())
                .studentId(attempt.getStudentId())
                .status(attempt.getStatus())
                .startedAt(attempt.getStartedAt())
                .submittedAt(attempt.getSubmittedAt())
                .score(attempt.getScore())
                .maxScore(attempt.getMaxScore())
                .build();
    }
}