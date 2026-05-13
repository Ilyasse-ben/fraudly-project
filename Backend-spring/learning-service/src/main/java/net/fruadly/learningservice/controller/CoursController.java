package net.fruadly.learningservice.controller;


import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.dto.CoursGetDto;
import net.fruadly.learningservice.dto.CoursPostDto;
import net.fruadly.learningservice.service.CoursService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/cours")
@RequiredArgsConstructor
public class CoursController {
    private final CoursService courseService;

    // Créer un nouveau cours
    @PostMapping
    @PreAuthorize("hasAnyAuthority('ROLE_TEACHER', 'ROLE_ADMIN')")
    public ResponseEntity<CoursPostDto> createCourse(@RequestBody CoursPostDto coursPostDto) {
        CoursPostDto createdPostCourse = courseService.createCourse(coursPostDto);
        return new ResponseEntity<>(createdPostCourse, HttpStatus.CREATED);
    }

    // Récupérer tous les cours (pour le catalogue)
    @GetMapping
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<List<CoursGetDto>> getAllCourses() {
        return ResponseEntity.ok(courseService.getAllCourses());
    }

    // Récupérer un cours spécifique par son ID
    @GetMapping("/{id}")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<CoursGetDto> getCourseById(@PathVariable UUID id) {
        return ResponseEntity.ok(courseService.getCourseById(id));
    }

    // Mettre à jour un cours
    @PutMapping("/{id}")
    @PreAuthorize("hasAnyAuthority('ROLE_TEACHER', 'ROLE_ADMIN')")
    public ResponseEntity<CoursPostDto> updateCourse(@PathVariable UUID id, @RequestBody CoursPostDto coursPostDto) {
        return ResponseEntity.ok(courseService.updateCourse(id, coursPostDto));
    }

    // Supprimer un cours
    @DeleteMapping("/{id}")
    @PreAuthorize("hasAnyAuthority('ROLE_TEACHER', 'ROLE_ADMIN')")
    public ResponseEntity<Void> deleteCourse(@PathVariable UUID id) {
        courseService.deleteCourse(id);
        return ResponseEntity.noContent().build();
    }
}
