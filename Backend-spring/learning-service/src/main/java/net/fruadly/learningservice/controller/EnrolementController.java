package net.fruadly.learningservice.controller;

import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.dto.EnrollmentDto;
import net.fruadly.learningservice.service.EnrollmentService;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/enrolements")
@RequiredArgsConstructor
@Transactional

public class EnrolementController {
    private final EnrollmentService enrollmentService;
    @PostMapping("/{coursCode}")
    public ResponseEntity<EnrollmentDto> addUser(@PathVariable String coursCode, @RequestBody EnrollmentDto dto){
        EnrollmentDto enrollmentDto1=enrollmentService.addEnrollmentToCourse(coursCode,dto);
        return new ResponseEntity<>(enrollmentDto1, HttpStatus.CREATED);
    }
    @DeleteMapping("/{erolementId}")
    public ResponseEntity<Void> deleteUser(@PathVariable UUID erolementId){
        enrollmentService.removeEnrollmentToCourse(erolementId);
        return ResponseEntity.noContent().build();
    }
}
