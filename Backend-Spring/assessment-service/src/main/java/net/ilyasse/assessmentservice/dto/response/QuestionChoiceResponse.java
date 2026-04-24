package net.ilyasse.assessmentservice.dto.response;

import lombok.Builder;
import lombok.Data;

/**
 * @author ELHAID Yousef
 **/
@Data
@Builder
public class QuestionChoiceResponse {
    private Long id;
    private String label;
    private String text;
    private Boolean isCorrect;
}
