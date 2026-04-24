package net.ilyasse.assessmentservice.dto.request;

import lombok.Data;

/**
 * @author ELHAID Yousef
 **/
@Data
public class UpdateChoiceRequest {
    private Long id;
    private String label;
    private String text;
    private Boolean isCorrect;
}