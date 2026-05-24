package net.ilyasse.proctoringservice.entity;

import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

@Entity
@Table(name = "collusion_pairs")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CollusionPair {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "alert_id", nullable = false)
    private CollusionAlert alert;

    private UUID questionId;
    private UUID studentAId;
    private UUID studentBId;

    private String studentAName;
    private String studentBName;

    @Column(nullable = false)
    private Double similarityScore;

    @Column(columnDefinition = "TEXT")
    private String answerAPreview;

    @Column(columnDefinition = "TEXT")
    private String answerBPreview;
}
