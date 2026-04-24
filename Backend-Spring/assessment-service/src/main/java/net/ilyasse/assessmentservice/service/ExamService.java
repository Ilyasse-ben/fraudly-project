package net.ilyasse.assessmentservice.service;

import net.ilyasse.assessmentservice.dto.request.ExamConfigRequest;
import net.ilyasse.assessmentservice.dto.request.UpdateQuestionRequest;
import net.ilyasse.assessmentservice.dto.response.ExamResponse;

import java.util.List;

/**
 * @author ELHAID Yousef
 **/
public interface ExamService {
    ExamResponse createExam(ExamConfigRequest request);
    ExamResponse getExamById(Long examId);
    List<ExamResponse> getExamsByProfessor(Long professorId);
    List<ExamResponse> getExamsByCourse(Long courseId);
    ExamResponse updateQuestion(Long questionId, UpdateQuestionRequest request, Long professorId);
    ExamResponse deleteQuestion(Long questionId, Long examId);
    ExamResponse validateExam(Long examId);
    ExamResponse publishExam(Long examId);
}