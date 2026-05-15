package net.fruadly.learningservice.dto;

import lombok.Data;

@Data
public class TutorAskResponse {

    private String question;
    private String answer;
    private Integer chunksUsed;
    private String provider;
}
