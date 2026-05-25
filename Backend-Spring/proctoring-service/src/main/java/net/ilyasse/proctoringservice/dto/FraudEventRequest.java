package net.ilyasse.proctoringservice.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;
import net.ilyasse.proctoringservice.enums.FraudEventType;

import java.util.UUID;

@Data
public class FraudEventRequest {
    @NotNull private UUID sessionId;
    @NotNull private FraudEventType eventType;
    @NotNull private Double confidenceScore;
    private String details;
}