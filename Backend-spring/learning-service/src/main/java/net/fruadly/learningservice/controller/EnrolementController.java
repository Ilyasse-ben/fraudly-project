package net.fruadly.learningservice.controller;

import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.dto.EnrollmentDto;
import net.fruadly.learningservice.security.SecurityPrincipalUtils;
import net.fruadly.learningservice.service.EnrollmentService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/learning/enrolements")
@RequiredArgsConstructor
@Transactional

public class EnrolementController {
    private final EnrollmentService enrollmentService;
    private final SecurityPrincipalUtils securityPrincipalUtils;

    @PostMapping("/{coursCode}")
    @PreAuthorize("hasAnyAuthority('ROLE_STUDENT', 'ROLE_TEACHER', 'ROLE_ADMIN')")
    public ResponseEntity<EnrollmentDto> addUser(@PathVariable String coursCode){
        UUID userId = securityPrincipalUtils.requireUserId();
        EnrollmentDto enrollmentDto1 = enrollmentService.addEnrollmentToCourse(coursCode, userId);
        return new ResponseEntity<>(enrollmentDto1, HttpStatus.CREATED);
    }
    @DeleteMapping("/{erolementId}")
    @PreAuthorize("hasAnyAuthority('ROLE_STUDENT', 'ROLE_TEACHER', 'ROLE_ADMIN')")
    public ResponseEntity<Void> deleteUser(@PathVariable UUID erolementId){
        enrollmentService.removeEnrollmentToCourse(erolementId);
        return ResponseEntity.noContent().build();
    }
}
