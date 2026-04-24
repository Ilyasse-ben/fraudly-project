package net.ilyasse.assessmentservice.dto.request;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;

/**
 * @author ELHAID Yousef
 **/
@Data
public class SubmitAttemptRequest {

    @NotNull
    private Long attemptId;

    @NotNull
    private List<SubmitAnswerRequest> answers;
}
