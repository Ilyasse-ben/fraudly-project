package net.ilyasse.assessmentservice.dto.request;

import jakarta.validation.constraints.NotNull;
import lombok.Data;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/
@Data
public class StartAttemptRequest {

    @NotNull
    private UUID studentId;

    @NotNull
    private UUID examId;
}
