package net.fruadly.learningservice.service;

import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.dto.EnrollmentDto;
import net.fruadly.learningservice.dto.UserDto;
import net.fruadly.learningservice.entity.Cours;
import net.fruadly.learningservice.entity.Enrollment;
import net.fruadly.learningservice.mapper.EnrollmentMapper;
import net.fruadly.learningservice.repository.CoursRepository;
import net.fruadly.learningservice.repository.EnrollmentRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.util.Date;
import java.util.UUID;

import static org.springframework.http.HttpStatus.CONFLICT;
import static org.springframework.http.HttpStatus.NOT_FOUND;
@Service
@RequiredArgsConstructor
@Transactional
public class EnrollmentService {

    private final CoursRepository coursRepository;
    private final EnrollmentMapper enrollmentMapper;
    private final EnrollmentRepository enrollmentRepository;
    private final UserCacheService userCacheService;

    public EnrollmentDto addEnrollmentToCourse(String coursCode, UUID studentId) {
        if (!coursRepository.existsByCoursCode(coursCode)) {
            throw new ResponseStatusException(NOT_FOUND, "Cours introuvable");
        }
        Cours cours = coursRepository.findByCoursCode(coursCode);

        UserDto user = userCacheService.getUser(studentId);
        if (user == null || user.getId() == null) {
            throw new ResponseStatusException(NOT_FOUND, "Utilisateur introuvable");
        }

        if (enrollmentRepository.existsByCourseIdAndStudentId(cours.getId(), studentId)) {
            throw new ResponseStatusException(CONFLICT, "Etudiant deja inscrit a ce cours");
        }

        Enrollment enrollment = new Enrollment();
        enrollment.setStudentId(studentId);
        enrollment.setEnrollmentDate(new Date());
        enrollment.setCourse(cours);

        return enrollmentMapper.toDto(enrollmentRepository.save(enrollment));
    }

    // Backward-compatible overload for existing callers passing DTO studentId.
    public EnrollmentDto addEnrollmentToCourse(String coursCode, EnrollmentDto dto) {
        return addEnrollmentToCourse(coursCode, dto.getStudentId());
    }

    public void removeEnrollmentToCourse(UUID id) {
        if (!enrollmentRepository.existsById(id)) {
            throw new ResponseStatusException(NOT_FOUND, "Inscription introuvable");
        }
        enrollmentRepository.deleteById(id);

    }
}
