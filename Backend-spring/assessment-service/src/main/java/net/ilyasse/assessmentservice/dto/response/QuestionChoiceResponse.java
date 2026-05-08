package net.ilyasse.assessmentservice.dto.response;

import lombok.Builder;
import lombok.Data;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/
@Data
@Builder
public class QuestionChoiceResponse {
    private UUID id;
    private String label;
    private String text;
    private Boolean isCorrect;
}
