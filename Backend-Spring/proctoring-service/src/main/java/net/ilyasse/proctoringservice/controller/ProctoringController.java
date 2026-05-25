package net.ilyasse.proctoringservice.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import net.ilyasse.proctoringservice.dto.*;
import net.ilyasse.proctoringservice.service.ProctoringSessionService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/proctoring")
@RequiredArgsConstructor
public class ProctoringController {

    private final ProctoringSessionService sessionService;

    // --- Session endpoints ---

    @PostMapping("/sessions/start")
    @PreAuthorize("hasAnyRole('STUDENT', 'TEACHER')")
    public ResponseEntity<ProctoringSessionResponse> startSession(
            @Valid @RequestBody StartSessionRequest request) {
        return ResponseEntity.ok(sessionService.startSession(request));
    }

    @PutMapping("/sessions/{sessionId}/end")
    @PreAuthorize("hasRole('STUDENT')")
    public ResponseEntity<ProctoringSessionResponse> endSession(
            @PathVariable UUID sessionId) {
        return ResponseEntity.ok(sessionService.endSession(sessionId));
    }

    @GetMapping("/sessions/{sessionId}")
    @PreAuthorize("hasAnyRole('STUDENT', 'TEACHER')")
    public ResponseEntity<ProctoringSessionResponse> getSession(
            @PathVariable UUID sessionId) {
        return ResponseEntity.ok(sessionService.getSession(sessionId));
    }

    @GetMapping("/sessions/{sessionId}/score")
    @PreAuthorize("hasRole('TEACHER')")
    public ResponseEntity<Integer> getLiveFraudScore(
            @PathVariable UUID sessionId) {
        return ResponseEntity.ok(sessionService.getLiveFraudScore(sessionId));
    }

    @GetMapping("/sessions/student/{studentId}")
    @PreAuthorize("hasRole('TEACHER')")
    public ResponseEntity<List<ProctoringSessionResponse>> getByStudent(
            @PathVariable UUID studentId) {
        return ResponseEntity.ok(sessionService.getSessionsByStudent(studentId));
    }

    @GetMapping("/sessions/exam/{examId}")
    @PreAuthorize("hasRole('TEACHER')")
    public ResponseEntity<List<ProctoringSessionResponse>> getByExam(
            @PathVariable UUID examId) {
        return ResponseEntity.ok(sessionService.getSessionsByExam(examId));
    }

    @GetMapping("/sessions/flagged")
    @PreAuthorize("hasRole('TEACHER')")
    public ResponseEntity<List<ProctoringSessionResponse>> getFlagged() {
        return ResponseEntity.ok(sessionService.getFlaggedSessions());
    }

    // --- Fraud event endpoints ---

    @PostMapping("/events")
    @PreAuthorize("hasAnyRole('STUDENT', 'TEACHER')")
    public ResponseEntity<FraudEventResponse> reportFraudEvent(
            @Valid @RequestBody FraudEventRequest request) {
        return ResponseEntity.ok(sessionService.reportFraudEvent(request));
    }

    @GetMapping("/events/session/{sessionId}")
    @PreAuthorize("hasRole('TEACHER')")
    public ResponseEntity<List<FraudEventResponse>> getEventsBySession(
            @PathVariable UUID sessionId) {
        return ResponseEntity.ok(sessionService.getEventsBySession(sessionId));
    }
}