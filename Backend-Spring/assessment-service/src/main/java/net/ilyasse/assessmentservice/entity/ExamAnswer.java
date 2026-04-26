package net.ilyasse.assessmentservice.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

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
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne
    @JoinColumn(name = "attempt_id", nullable = false)
    private ExamAttempt attempt;

    @ManyToOne
    @JoinColumn(name = "question_id", nullable = false)
    private ExamQuestion question;

    @Column(columnDefinition = "TEXT")
    private String answerText;

    private UUID selectedChoiceId;
    private Boolean isCorrect;
    private Double pointsAwarded;
    private Boolean isGraded = false;
    private LocalDateTime answeredAt;
    private Boolean modifiedByProfessor = false;
    private Double originalAiScore;
    private UUID modifiedByProfessorId;
    private LocalDateTime modifiedAt;

    @PrePersist
    protected void onCreate() {
        this.answeredAt = LocalDateTime.now();
    }
}
