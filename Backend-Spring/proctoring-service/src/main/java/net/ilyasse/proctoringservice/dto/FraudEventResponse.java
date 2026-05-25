package net.ilyasse.proctoringservice.dto;

import lombok.Builder;
import lombok.Data;
import net.ilyasse.proctoringservice.enums.FraudEventType;

import java.time.LocalDateTime;
import java.util.UUID;

@Data
@Builder
public class FraudEventResponse {
    private UUID id;
    private UUID sessionId;
    private UUID studentId;
    private UUID examId;
    private FraudEventType eventType;
    private Double confidenceScore;
    private String details;
    private LocalDateTime detectedAt;
}