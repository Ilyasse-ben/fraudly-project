package net.ilyasse.proctoringservice.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.UUID;

@Data
public class StartSessionRequest {
    @NotNull private UUID studentId;
    @NotNull private UUID examId;
    @NotNull private UUID attemptId;
    private String deviceFingerprint;
}