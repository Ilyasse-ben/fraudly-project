package net.fruadly.learningservice.dto;

import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import lombok.Data;
import net.fruadly.learningservice.entity.Cours;

import java.util.Date;
import java.util.UUID;

@Data
public class EnrollmentDto {
    private UUID id;
    private UUID studentId;
    private Date enrollmentDate ;
}
