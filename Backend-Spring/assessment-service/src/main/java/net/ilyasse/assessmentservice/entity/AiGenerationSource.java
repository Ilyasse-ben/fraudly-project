package net.ilyasse.assessmentservice.entity;

import jakarta.persistence.*;
import lombok.*;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/

@Entity
@Table(name = "ai_generation_sources")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class AiGenerationSource {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne
    @JoinColumn(name = "exam_id", nullable = false)
    private Exam exam;

    @Column(nullable = false)
    private String sourceFile;

    private Integer page;
    private Double score;

    @Column(columnDefinition = "TEXT")
    private String excerpt;

    @Column(nullable = false)
    private Boolean isRagContext = false;
}
