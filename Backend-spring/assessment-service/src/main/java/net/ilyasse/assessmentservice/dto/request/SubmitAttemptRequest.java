package net.ilyasse.assessmentservice.dto.request;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/
@Data
public class SubmitAttemptRequest {

    @NotNull
    private UUID attemptId;

    @NotNull
    private List<SubmitAnswerRequest> answers;
}
