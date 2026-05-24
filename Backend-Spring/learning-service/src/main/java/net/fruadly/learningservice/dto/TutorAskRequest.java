package net.fruadly.learningservice.dto;

import lombok.Data;

@Data
public class TutorAskRequest {

    private String question;
    private String courseId;
    private String chapterId;
    private Integer topK = 5;
}