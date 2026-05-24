package net.ilyasse.assessmentservice.dto.request;


import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import java.util.List;
/**
 * @author ELHAID Yousef
 **/

@Data
public class UpdateQuestionRequest {

    @NotBlank
    private String questionText;

    private String correctAnswer;
    private String explanation;
    private Integer points;
    private String reason;
    private List<UpdateChoiceRequest> choices;
}
