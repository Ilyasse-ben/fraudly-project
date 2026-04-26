package net.ilyasse.assessmentservice.entity;

import jakarta.persistence.*;
import lombok.*;
import net.ilyasse.assessmentservice.enums.AttemptStatus;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/

@Entity
@Table(name = "exam_attempts")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class ExamAttempt {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne
    @JoinColumn(name = "exam_id", nullable = false)
    private Exam exam;

    @Column(nullable = false)
    private UUID studentId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private AttemptStatus status;

    private LocalDateTime startedAt;
    private LocalDateTime submittedAt;
    private Double score;
    private Double maxScore;

    @PrePersist
    protected void onCreate() {
        if (this.status == null) this.status = AttemptStatus.STARTED;
        this.startedAt = LocalDateTime.now();
    }
}
