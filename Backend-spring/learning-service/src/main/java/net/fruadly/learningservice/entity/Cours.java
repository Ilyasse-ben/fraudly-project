package net.fruadly.learningservice.entity;

import jakarta.persistence.*;
import lombok.*;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.UUID;

@Entity @Getter @Setter @NoArgsConstructor @AllArgsConstructor @ToString
@Table(name = "courses")
public class Cours {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    private String title;
    @Column(columnDefinition = "TEXT")
    private String description;
    private String category;
    private Date courseDate ;
    // ID provenant du service d'authentification
    private UUID profId;

    @OneToMany(mappedBy = "cours", cascade = CascadeType.ALL, orphanRemoval = true)
    @OrderBy("index")
    private List<Chapter> chapters = new ArrayList<>();
    @OneToMany(mappedBy = "course")
    private List<Enrollment> enrollments = new ArrayList<>();
}
