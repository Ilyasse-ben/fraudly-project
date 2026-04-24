package net.ilyasse.assessmentservice.dto.request;

import lombok.Data;

import java.util.List;

/**
 * @author ELHAID Yousef
 **/
@Data
public class SubmitAnswerRequest {
    private Long questionId;
    private String answerText;
    private Long selectedChoiceId;
    private List<Long> selectedChoiceIds;
}
