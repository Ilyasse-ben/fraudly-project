package net.ilyasse.assessmentservice.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class BackendAiGenerationRequest {

    private String topic;

    @JsonProperty("course_id")
    private String courseId;

    @JsonProperty("chapter_ids")
    private List<String> chapterIds;

    private String difficulty;

    @JsonProperty("total_questions")
    private Integer totalQuestions;

    @JsonProperty("qcm_count")
    private Integer qcmCount;

    @JsonProperty("true_false_count")
    private Integer trueFalseCount;

    @JsonProperty("open_count")
    private Integer openCount;

    @JsonProperty("include_explanations")
    private Boolean includeExplanations;

    @JsonProperty("professor_instructions")
    private String professorInstructions;

    @JsonProperty("top_k")
    private Integer topK;
}