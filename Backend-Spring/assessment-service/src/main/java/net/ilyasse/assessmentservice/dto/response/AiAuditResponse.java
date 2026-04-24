package net.ilyasse.assessmentservice.dto.response;


import lombok.Builder;
import lombok.Data;
import java.time.LocalDateTime;

/**
 * @author ELHAID Yousef
 **/
@Data
@Builder
public class AiAuditResponse {
    private String provider;
    private Boolean fallbackUsed;
    private Integer retrievedChunks;
    private Integer promptChars;
    private Integer generatedQuestions;
    private String requestedDifficulty;
    private LocalDateTime generatedAt;
}