package net.ilyasse.assessmentservice.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.List;
/**
 * @author ELHAID Yousef
 **/

@Data
public class AiGenerationResponse {

    private String topic;
    private String difficulty;

    @JsonProperty("total_requested")
    private Integer totalRequested;

    @JsonProperty("total_generated")
    private Integer totalGenerated;

    private List<AiQuestion> questions;
    private List<AiSource> sources;

    @JsonProperty("rag_context")
    private List<AiRagContext> ragContext;

    private AiAudit audit;

    @Data
    public static class AiQuestion {
        private Integer id;
        private String type;
        private String difficulty;
        private String question;
        private List<AiChoice> choices;

        @JsonProperty("correct_answer")
        private String correctAnswer;

        private String explanation;
    }

    @Data
    public static class AiChoice {
        private String label;
        private String text;

        @JsonProperty("is_correct")
        private Boolean isCorrect;
    }

    @Data
    public static class AiSource {
        @JsonProperty("source_file")
        private String sourceFile;

        private Integer page;
        private Double score;
    }

    @Data
    public static class AiRagContext {
        @JsonProperty("source_file")
        private String sourceFile;

        private Integer page;
        private Double score;
        private String excerpt;
    }

    @Data
    public static class AiAudit {
        private String provider;

        @JsonProperty("fallback_used")
        private Boolean fallbackUsed;

        @JsonProperty("retrieved_chunks")
        private Integer retrievedChunks;

        @JsonProperty("prompt_chars")
        private Integer promptChars;

        @JsonProperty("generated_questions")
        private Integer generatedQuestions;

        @JsonProperty("requested_difficulty")
        private String requestedDifficulty;
    }
}

