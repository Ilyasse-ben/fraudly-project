package net.ilyasse.assessmentservice.dto.response;

import lombok.Builder;
import lombok.Data;
import net.ilyasse.assessmentservice.enums.AttemptStatus;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/
@Data
@Builder
public class ExamAttemptResponse {
    private UUID id;
    private UUID examId;
    private UUID studentId;
    private AttemptStatus status;
    private LocalDateTime startedAt;
    private LocalDateTime submittedAt;
    private Double score;
    private Double maxScore;
}