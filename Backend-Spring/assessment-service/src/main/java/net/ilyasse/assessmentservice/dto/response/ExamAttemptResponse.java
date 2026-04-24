package net.ilyasse.assessmentservice.dto.response;

import lombok.Builder;
import lombok.Data;
import net.ilyasse.assessmentservice.enums.AttemptStatus;
import java.time.LocalDateTime;

/**
 * @author ELHAID Yousef
 **/
@Data
@Builder
public class ExamAttemptResponse {
    private Long id;
    private Long examId;
    private Long studentId;
    private AttemptStatus status;
    private LocalDateTime startedAt;
    private LocalDateTime submittedAt;
    private Double score;
    private Double maxScore;
}