package net.ilyasse.assessmentservice.controller;

import lombok.RequiredArgsConstructor;
import net.ilyasse.assessmentservice.dto.request.ExamConfigRequest;
import net.ilyasse.assessmentservice.dto.request.StartAttemptRequest;
import net.ilyasse.assessmentservice.dto.request.SubmitAttemptRequest;
import net.ilyasse.assessmentservice.dto.request.UpdateQuestionRequest;
import net.ilyasse.assessmentservice.dto.response.ExamAttemptResponse;
import net.ilyasse.assessmentservice.dto.response.ExamResponse;
import net.ilyasse.assessmentservice.service.ExamAttemptService;
import net.ilyasse.assessmentservice.service.ExamService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/exams")
@RequiredArgsConstructor
public class ExamController {

    private final ExamService examService;
    private final ExamAttemptService examAttemptService;


    @PostMapping("/generate")
    public ResponseEntity<ExamResponse> createExam(@RequestBody ExamConfigRequest request) {
        return ResponseEntity.ok(examService.createExam(request));
    }

    @GetMapping("/{examId}")
    public ResponseEntity<ExamResponse> getExam(@PathVariable UUID examId) {
        return ResponseEntity.ok(examService.getExamById(examId));
    }

    @GetMapping("/professor/{professorId}")
    public ResponseEntity<List<ExamResponse>> getExamsByProfessor(@PathVariable UUID professorId) {
        return ResponseEntity.ok(examService.getExamsByProfessor(professorId));
    }

    @GetMapping("/course/{courseId}")
    public ResponseEntity<List<ExamResponse>> getExamsByCourse(@PathVariable UUID courseId) {
        return ResponseEntity.ok(examService.getExamsByCourse(courseId));
    }

    @PutMapping("/questions/{questionId}")
    public ResponseEntity<ExamResponse> updateQuestion(
            @PathVariable UUID questionId,
            @RequestBody UpdateQuestionRequest request,
            @RequestParam UUID professorId) {
        return ResponseEntity.ok(examService.updateQuestion(questionId, request, professorId));
    }

    @DeleteMapping("/questions/{questionId}")
    public ResponseEntity<ExamResponse> deleteQuestion(
            @PathVariable UUID questionId,
            @RequestParam UUID examId) {
        return ResponseEntity.ok(examService.deleteQuestion(questionId, examId));
    }

    @PutMapping("/{examId}/validate")
    public ResponseEntity<ExamResponse> validateExam(@PathVariable UUID examId) {
        return ResponseEntity.ok(examService.validateExam(examId));
    }

    @PutMapping("/{examId}/publish")
    public ResponseEntity<ExamResponse> publishExam(@PathVariable UUID examId) {
        return ResponseEntity.ok(examService.publishExam(examId));
    }


    @PostMapping("/{examId}/correction")
    public ResponseEntity<Void> launchCorrection(
            @PathVariable UUID examId,
            @RequestParam UUID professorId) {
        examService.launchCorrection(examId, professorId);
        return ResponseEntity.accepted().build();
    }


    @PostMapping("/attempts/start")
    public ResponseEntity<ExamAttemptResponse> startAttempt(@RequestBody StartAttemptRequest request) {
        return ResponseEntity.ok(examAttemptService.startAttempt(request));
    }

    @PostMapping("/attempts/submit")
    public ResponseEntity<ExamAttemptResponse> submitAttempt(@RequestBody SubmitAttemptRequest request) {
        return ResponseEntity.ok(examAttemptService.submitAttempt(request));
    }

    @GetMapping("/attempts/{attemptId}")
    public ResponseEntity<ExamAttemptResponse> getAttempt(@PathVariable UUID attemptId) {
        return ResponseEntity.ok(examAttemptService.getAttemptById(attemptId));
    }

    @GetMapping("/attempts/student/{studentId}")
    public ResponseEntity<List<ExamAttemptResponse>> getAttemptsByStudent(@PathVariable UUID studentId) {
        return ResponseEntity.ok(examAttemptService.getAttemptsByStudent(studentId));
    }

    @GetMapping("/attempts/exam/{examId}")
    public ResponseEntity<List<ExamAttemptResponse>> getAttemptsByExam(@PathVariable UUID examId) {
        return ResponseEntity.ok(examAttemptService.getAttemptsByExam(examId));
    }
    @GetMapping("/{examId}/open-answers")
    public ResponseEntity<List<Map<String, Object>>> getOpenAnswers(@PathVariable UUID examId) {
        return ResponseEntity.ok(examService.getOpenAnswers(examId));
    }
    @PatchMapping("/answers/{answerId}/score")
    public ResponseEntity<Void> updateAnswerScore(
            @PathVariable UUID answerId,
            @RequestParam Double pointsAwarded,
            @RequestParam UUID professorId) {
        examService.updateAnswerScore(answerId, pointsAwarded, professorId);
        return ResponseEntity.ok().build();
    }
}