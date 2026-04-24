package net.ilyasse.assessmentservice.entity;


import jakarta.persistence.*;
import lombok.*;
import net.ilyasse.assessmentservice.enums.Difficulty;
import net.ilyasse.assessmentservice.enums.QuestionType;
import java.time.LocalDateTime;

/**
 * @author ELHAID Yousef
 **/

@Entity
@Table(name = "exam_configs")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class ExamConfig {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne
    @JoinColumn(name = "exam_id", nullable = false)
    private Exam exam;

    @Column(nullable = false)
    private Integer nbQcm;

    @Enumerated(EnumType.STRING)
    private QuestionType qcmType;

    @Column(nullable = false)
    private Integer nbTrueFalse;

    @Column(nullable = false)
    private Integer nbOpen;

    @Column(columnDefinition = "TEXT")
    private String chapterIds;

    @Enumerated(EnumType.STRING)
    private Difficulty difficulty;

    @Column(nullable = false)
    private String configStatus = "PENDING";

    private LocalDateTime requestedAt;

    @PrePersist
    protected void onCreate() {
        this.requestedAt = LocalDateTime.now();
    }
}
