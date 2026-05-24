package net.fruadly.learningservice.mapper;

import net.fruadly.learningservice.dto.EnrollmentDto;
import net.fruadly.learningservice.entity.Enrollment;
import org.springframework.stereotype.Component;

@Component
public class EnrollmentMapper {
    public EnrollmentDto toDto(Enrollment entity) {
        if (entity == null) return null;

        EnrollmentDto dto = new EnrollmentDto();
        dto.setId(entity.getId());
        dto.setEnrollmentDate(entity.getEnrollmentDate());
        dto.setStudentId(entity.getStudentId());

        return dto;
    }

    public Enrollment toEntity(EnrollmentDto dto) {
        if (dto == null) return null;
        Enrollment entity = new Enrollment();
        entity.setStudentId(dto.getStudentId());
        entity.setEnrollmentDate(dto.getEnrollmentDate());
        return entity;
    }
}
