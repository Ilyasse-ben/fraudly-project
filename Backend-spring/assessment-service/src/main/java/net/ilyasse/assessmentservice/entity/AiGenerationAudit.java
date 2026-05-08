package net.ilyasse.assessmentservice.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/

@Entity
@Table(name = "ai_generation_audits")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class AiGenerationAudit {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @OneToOne
    @JoinColumn(name = "exam_id", nullable = false)
    private Exam exam;

    private String provider;
    private Boolean fallbackUsed;
    private Integer retrievedChunks;
    private Integer promptChars;
    private Integer generatedQuestions;
    private String requestedDifficulty;

    @Column(nullable = false)
    private LocalDateTime generatedAt;

    @PrePersist
    protected void onCreate() {
        this.generatedAt = LocalDateTime.now();
    }
}

