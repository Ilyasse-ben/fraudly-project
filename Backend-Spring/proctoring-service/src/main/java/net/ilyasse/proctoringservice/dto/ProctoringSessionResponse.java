package net.ilyasse.proctoringservice.dto;

import lombok.Builder;
import lombok.Data;
import net.ilyasse.proctoringservice.enums.SessionStatus;

import java.time.LocalDateTime;
import java.util.UUID;

@Data
@Builder
public class ProctoringSessionResponse {
    private UUID id;
    private UUID studentId;
    private UUID examId;
    private UUID attemptId;
    private SessionStatus status;
    private Integer fraudScore;
    private String deviceFingerprint;
    private LocalDateTime startedAt;
    private LocalDateTime endedAt;
}