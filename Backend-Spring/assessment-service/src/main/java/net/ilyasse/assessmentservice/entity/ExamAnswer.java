package net.ilyasse.assessmentservice.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

/**
 * @author ELHAID Yousef
 **/

@Entity
@Table(name = "exam_answers")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class ExamAnswer {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "attempt_id", nullable = false)
    private ExamAttempt attempt;

    @ManyToOne
    @JoinColumn(name = "question_id", nullable = false)
    private ExamQuestion question;

    @Column(columnDefinition = "TEXT")
    private String answerText;

    private Long selectedChoiceId;
    private Boolean isCorrect;
    private Double pointsAwarded;
    private Boolean isGraded = false;
    private LocalDateTime answeredAt;

    @PrePersist
    protected void onCreate() {
        this.answeredAt = LocalDateTime.now();
    }
}
