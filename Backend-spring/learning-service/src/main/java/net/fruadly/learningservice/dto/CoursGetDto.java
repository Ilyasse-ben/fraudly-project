package net.fruadly.learningservice.dto;

import lombok.Data;
import net.fruadly.learningservice.entity.Chapter;
import net.fruadly.learningservice.entity.Enrollment;

import java.util.List;
import java.util.UUID;

@Data
public class CoursGetDto {
    private UUID id;
    private String title;
    private String description;
    private String category;
    private UUID profId;
    // On peut ajouter un champ calculé pour le dashboard
    private Integer chapterCount;
    private String coursCode;
    // Ajout de la liste pour la vue détaillée
    private List<Chapter> chapters;
    private List<Enrollment> enrollments;
}
