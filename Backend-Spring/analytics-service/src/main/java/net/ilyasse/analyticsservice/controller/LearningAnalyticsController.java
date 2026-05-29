package net.ilyasse.analyticsservice.controller;

import lombok.RequiredArgsConstructor;
import net.ilyasse.analyticsservice.dto.StudentGradeDto;
import net.ilyasse.analyticsservice.service.LearningAnalyticsService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/analytics")
@RequiredArgsConstructor
public class LearningAnalyticsController {
    private final LearningAnalyticsService learningAnalyticsService;

    @GetMapping("/students/{studentId}/profile")
    public ResponseEntity<Map<String, Object>> getStudentProfile(
            @PathVariable UUID studentId,
            @RequestParam(required = false) UUID courseId) {
        return ResponseEntity.ok(
                learningAnalyticsService.getStudentProfile(studentId, courseId)
        );
    }

    // Weak topics d'un étudiant pour un cours
    @GetMapping("/students/{studentId}/weak-topics")
    public ResponseEntity<List<String>> getWeakTopics(
            @PathVariable UUID studentId,
            @RequestParam UUID courseId,
            @RequestParam(defaultValue = "3") int minCount) {
        return ResponseEntity.ok(
                learningAnalyticsService.getWeakTopics(studentId, courseId, minCount)
        );
    }

    // Stats topics pour un cours (dashboard prof)
    @GetMapping("/courses/{courseId}/topics")
    public ResponseEntity<List<Map<String, Object>>> getCourseTopicStats(
            @PathVariable UUID courseId) {
        return ResponseEntity.ok(
                learningAnalyticsService.getCourseTopicStats(courseId)
        );
    }
    // Inside LearningAnalyticsController.java

    @GetMapping("/courses/{courseId}/grades")
    public ResponseEntity<List<StudentGradeDto>> getStudentsGrades(@PathVariable UUID courseId) {
        return ResponseEntity.ok(learningAnalyticsService.getStudentsGrades(courseId));
    }

}
