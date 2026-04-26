package net.ilyasse.assessmentservice.dto.request;

import lombok.Data;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/
@Data
public class UpdateChoiceRequest {
    private UUID id;
    private String label;
    private String text;
    private Boolean isCorrect;
}