package net.fruadly.learningservice.service;

import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.dto.ChapitrDto;
import net.fruadly.learningservice.dto.EnrollmentDto;
import net.fruadly.learningservice.entity.Cours;
import net.fruadly.learningservice.entity.Enrollment;
import net.fruadly.learningservice.mapper.EnrollmentMapper;
import net.fruadly.learningservice.repository.CoursRepository;
import net.fruadly.learningservice.repository.EnrollmentRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;
import java.util.UUID;
@Service
@RequiredArgsConstructor
@Transactional
public class EnrollmentService {

    private final CoursRepository coursRepository;
    private final EnrollmentMapper enrollmentMapper;
    private final EnrollmentRepository enrollmentRepository;
    public EnrollmentDto addEnrollmentToCourse(String coursCode, EnrollmentDto dto) {
        if(!coursRepository.existsByCoursCode(coursCode)){
            throw new RuntimeException("le cours  est déja existe en ");
        }
        Cours cours = coursRepository.findByCoursCode(coursCode);


        if(enrollmentRepository.existsByCourseIdAndStudentId(cours.getId(),dto.getStudentId())){
            throw new RuntimeException("l'étudient est déja existe en ce cours ");
        }




        Enrollment enrollment = enrollmentMapper.toEntity(dto);
        enrollment.setEnrollmentDate(new Date());
        enrollment.setCourse(cours);

        return enrollmentMapper.toDto(enrollmentRepository.save(enrollment));
    }
    public void removeEnrollmentToCourse(UUID id) {
        if (!enrollmentRepository.existsById(id)) {
            throw new RuntimeException("Impossible de supprimer : l'etudient n'existe pas");
        }
        enrollmentRepository.deleteById(id);

    }
}
