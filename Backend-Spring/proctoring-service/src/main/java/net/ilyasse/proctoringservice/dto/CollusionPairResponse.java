package net.ilyasse.proctoringservice.dto;

import lombok.Builder;
import lombok.Data;

import java.util.UUID;

@Data
@Builder
public class CollusionPairResponse {
    private UUID id;
    private UUID questionId;
    private UUID studentAId;
    private UUID studentBId;
    private String studentAName;
    private String studentBName;
    private Double similarityScore;
    private String answerAPreview;
    private String answerBPreview;
}
