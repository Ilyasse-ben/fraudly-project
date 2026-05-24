package net.ilyasse.proctoringservice.controller;

import lombok.RequiredArgsConstructor;
import net.ilyasse.proctoringservice.dto.CollusionAlertResponse;
import net.ilyasse.proctoringservice.service.CollusionAlertService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/proctoring/collusions")
@RequiredArgsConstructor
public class CollusionAlertController {

    private final CollusionAlertService collusionAlertService;

    @GetMapping
    public ResponseEntity<List<CollusionAlertResponse>> getAll() {
        return ResponseEntity.ok(collusionAlertService.getAll());
    }

    @GetMapping("/exam/{examId}")
    public ResponseEntity<List<CollusionAlertResponse>> getByExam(@PathVariable UUID examId) {
        return ResponseEntity.ok(collusionAlertService.getByExamId(examId));
    }
}
