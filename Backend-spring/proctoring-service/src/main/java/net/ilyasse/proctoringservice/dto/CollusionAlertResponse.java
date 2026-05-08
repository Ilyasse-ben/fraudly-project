package net.ilyasse.proctoringservice.dto;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Data
@Builder
public class CollusionAlertResponse {
    private UUID id;
    private UUID examId;
    private UUID courseId;
    private LocalDateTime detectedAt;
    private Integer pairCount;
    private LocalDateTime createdAt;
    private List<CollusionPairResponse> suspectedPairs;
}
