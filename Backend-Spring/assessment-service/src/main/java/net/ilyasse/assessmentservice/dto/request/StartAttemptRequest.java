package net.ilyasse.assessmentservice.dto.request;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

/**
 * @author ELHAID Yousef
 **/
@Data
public class StartAttemptRequest {

    @NotNull
    private Long studentId;

    @NotNull
    private Long examId;
}
