package net.ilyasse.analyticsservice.dto;

import lombok.Builder;
import lombok.Data;
import java.util.UUID;

@Data
@Builder
public class StudentGradeDto {
    private UUID studentId;
    private String studentName;
    private Double cc1;
    private Double cc2;
    private Double exam;
    private Double average;
    private String status; // "Excellent" or "Needs Review"
}