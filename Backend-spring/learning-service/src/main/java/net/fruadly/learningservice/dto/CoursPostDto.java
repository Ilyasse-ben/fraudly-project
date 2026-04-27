package net.fruadly.learningservice.dto;

import lombok.Data;

import java.util.UUID;

@Data
public class CoursPostDto {
    private UUID id;
    private String title;
    private String description;
    private String category;
    private UUID profId;
}
