package net.ilyasse.assessmentservice.dto.request;

import lombok.Data;

import java.util.List;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/
@Data
public class SubmitAnswerRequest {
    private UUID questionId;
    private String answerText;
    private UUID selectedChoiceId;
    private List<UUID> selectedChoiceIds;
}
