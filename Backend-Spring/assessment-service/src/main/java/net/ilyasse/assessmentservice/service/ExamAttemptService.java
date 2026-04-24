package net.ilyasse.assessmentservice.service;

import net.ilyasse.assessmentservice.dto.request.StartAttemptRequest;
import net.ilyasse.assessmentservice.dto.request.SubmitAttemptRequest;
import net.ilyasse.assessmentservice.dto.response.ExamAttemptResponse;

import java.util.List;

/**
 * @author ELHAID Yousef
 **/
public interface ExamAttemptService {
    ExamAttemptResponse startAttempt(StartAttemptRequest request);
    ExamAttemptResponse submitAttempt(SubmitAttemptRequest request);
    ExamAttemptResponse getAttemptById(Long attemptId);
    List<ExamAttemptResponse> getAttemptsByStudent(Long studentId);
    List<ExamAttemptResponse> getAttemptsByExam(Long examId);
}