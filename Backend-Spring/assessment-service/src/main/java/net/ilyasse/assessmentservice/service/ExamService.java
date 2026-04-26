package net.ilyasse.assessmentservice.service;

import net.ilyasse.assessmentservice.dto.request.ExamConfigRequest;
import net.ilyasse.assessmentservice.dto.request.UpdateQuestionRequest;
import net.ilyasse.assessmentservice.dto.response.ExamResponse;

import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/
public interface ExamService {
    ExamResponse createExam(ExamConfigRequest request);
    ExamResponse getExamById(UUID examId);
    List<ExamResponse> getExamsByProfessor(UUID professorId);
    List<ExamResponse> getExamsByCourse(UUID courseId);
    ExamResponse updateQuestion(UUID questionId, UpdateQuestionRequest request, UUID professorId);
    ExamResponse deleteQuestion(UUID questionId, UUID examId);
    ExamResponse validateExam(UUID examId);
    ExamResponse publishExam(UUID examId);
    void launchCorrection(UUID examId, UUID professorId);
    List<Map<String, Object>> getOpenAnswers(UUID examId);
    void updateAnswerScore(UUID answerId, Double pointsAwarded, UUID professorId);
}