package net.ilyasse.assessmentservice.service;

import net.ilyasse.assessmentservice.dto.request.StartAttemptRequest;
import net.ilyasse.assessmentservice.dto.request.SubmitAttemptRequest;
import net.ilyasse.assessmentservice.dto.response.ExamAttemptResponse;

import java.util.List;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/
public interface ExamAttemptService {
    ExamAttemptResponse startAttempt(StartAttemptRequest request);
    ExamAttemptResponse submitAttempt(SubmitAttemptRequest request);
    ExamAttemptResponse getAttemptById(UUID attemptId);
    List<ExamAttemptResponse> getAttemptsByStudent(UUID studentId);
    List<ExamAttemptResponse> getAttemptsByExam(UUID examId);
}