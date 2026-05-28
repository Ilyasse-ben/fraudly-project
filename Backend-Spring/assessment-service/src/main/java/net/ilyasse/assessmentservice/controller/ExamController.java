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
import org.springframework.security.access.prepost.PreAuthorize;
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

    // --- EXAM MANAGEMENT (TEACHERS ONLY) ---

    @PostMapping("/generate")
    @PreAuthorize("hasAuthority('ROLE_TEACHER')")
    public ResponseEntity<ExamResponse> createExam(@RequestBody ExamConfigRequest request) {
        return ResponseEntity.ok(examService.createExam(request));
    }

    @GetMapping("/professor/{professorId}")
    @PreAuthorize("hasAuthority('ROLE_TEACHER')")
    public ResponseEntity<List<ExamResponse>> getExamsByProfessor(@PathVariable UUID professorId) {
        return ResponseEntity.ok(examService.getExamsByProfessor(professorId));
    }

    @PutMapping("/questions/{questionId}")
    @PreAuthorize("hasAuthority('ROLE_TEACHER')")
    public ResponseEntity<ExamResponse> updateQuestion(
            @PathVariable UUID questionId,
            @RequestBody UpdateQuestionRequest request,
            @RequestParam UUID professorId) {
        return ResponseEntity.ok(examService.updateQuestion(questionId, request, professorId));
    }

    @DeleteMapping("/questions/{questionId}")
    @PreAuthorize("hasAuthority('ROLE_TEACHER')")
    public ResponseEntity<ExamResponse> deleteQuestion(
            @PathVariable UUID questionId,
            @RequestParam UUID examId) {
        return ResponseEntity.ok(examService.deleteQuestion(questionId, examId));
    }

    @PutMapping("/{examId}/validate")
    @PreAuthorize("hasAuthority('ROLE_TEACHER')")
    public ResponseEntity<ExamResponse> validateExam(@PathVariable UUID examId) {
        return ResponseEntity.ok(examService.validateExam(examId));
    }

    @PutMapping("/{examId}/publish")
    @PreAuthorize("hasAuthority('ROLE_TEACHER')")
    public ResponseEntity<ExamResponse> publishExam(@PathVariable UUID examId) {
        return ResponseEntity.ok(examService.publishExam(examId));
    }

    @PostMapping("/{examId}/correction")
    @PreAuthorize("hasAuthority('ROLE_TEACHER')")
    public ResponseEntity<Void> launchCorrection(
            @PathVariable UUID examId,
            @RequestParam UUID professorId) {
        examService.launchCorrection(examId, professorId);
        return ResponseEntity.accepted().build();
    }

    @GetMapping("/{examId}/open-answers")
    @PreAuthorize("hasAuthority('ROLE_TEACHER')")
    public ResponseEntity<List<Map<String, Object>>> getOpenAnswers(@PathVariable UUID examId) {
        return ResponseEntity.ok(examService.getOpenAnswers(examId));
    }

    @PatchMapping("/answers/{answerId}/score")
    @PreAuthorize("hasAuthority('ROLE_TEACHER')")
    public ResponseEntity<Void> updateAnswerScore(
            @PathVariable UUID answerId,
            @RequestParam Double pointsAwarded,
            @RequestParam UUID professorId) {
        examService.updateAnswerScore(answerId, pointsAwarded, professorId);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/attempts/exam/{examId}")
    @PreAuthorize("hasAuthority('ROLE_TEACHER')")
    public ResponseEntity<List<ExamAttemptResponse>> getAttemptsByExam(@PathVariable UUID examId) {
        return ResponseEntity.ok(examAttemptService.getAttemptsByExam(examId));
    }


    // --- EXAM TAKING (STUDENTS ONLY) ---

    @PostMapping("/attempts/start")
    @PreAuthorize("hasAuthority('ROLE_STUDENT')")
    public ResponseEntity<ExamAttemptResponse> startAttempt(@RequestBody StartAttemptRequest request) {
        return ResponseEntity.ok(examAttemptService.startAttempt(request));
    }

    @PostMapping("/attempts/submit")
    @PreAuthorize("hasAuthority('ROLE_STUDENT')")
    public ResponseEntity<ExamAttemptResponse> submitAttempt(@RequestBody SubmitAttemptRequest request) {
        return ResponseEntity.ok(examAttemptService.submitAttempt(request));
    }


    // --- SHARED ACCESS (TEACHERS AND STUDENTS) ---

    @GetMapping("/{examId}")
    @PreAuthorize("hasAnyAuthority('ROLE_TEACHER', 'ROLE_STUDENT')")
    public ResponseEntity<ExamResponse> getExam(@PathVariable UUID examId) {
        return ResponseEntity.ok(examService.getExamById(examId));
    }

    @GetMapping("/course/{courseId}")
    @PreAuthorize("hasAnyAuthority('ROLE_TEACHER', 'ROLE_STUDENT')")
    public ResponseEntity<List<ExamResponse>> getExamsByCourse(@PathVariable UUID courseId) {
        return ResponseEntity.ok(examService.getExamsByCourse(courseId));
    }

    @GetMapping("/attempts/{attemptId}")
    @PreAuthorize("hasAnyAuthority('ROLE_TEACHER', 'ROLE_STUDENT')")
    public ResponseEntity<ExamAttemptResponse> getAttempt(@PathVariable UUID attemptId) {
        return ResponseEntity.ok(examAttemptService.getAttemptById(attemptId));
    }

    @GetMapping("/attempts/student/{studentId}")
    @PreAuthorize("hasAnyAuthority('ROLE_TEACHER', 'ROLE_STUDENT')")
    public ResponseEntity<List<ExamAttemptResponse>> getAttemptsByStudent(@PathVariable UUID studentId) {
        return ResponseEntity.ok(examAttemptService.getAttemptsByStudent(studentId));
    }
}