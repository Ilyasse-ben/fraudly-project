package net.fruadly.learningservice.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.UUID;

@Entity @Table(name = "chapters")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @ToString
public class Chapter {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    private String title;

    private Long index;
    private Date dateChapitre;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "course_id")
    @JsonIgnore
    private Cours cours;
    @OneToMany(mappedBy = "chapter", cascade = CascadeType.ALL)
    private List<Resource> resources = new ArrayList<>();
}
