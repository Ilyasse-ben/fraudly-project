package net.ilyasse.assessmentservice.entity;


import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
/**
 * @author ELHAID Yousef
 **/

@Entity
@Table(name = "question_revisions")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class QuestionRevision {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "question_id", nullable = false)
    private ExamQuestion question;

    @Column(nullable = false)
    private Long changedBy;

    @Column(nullable = false)
    private LocalDateTime changedAt;

    private String fieldChanged;

    @Column(columnDefinition = "TEXT")
    private String oldValue;

    @Column(columnDefinition = "TEXT")
    private String newValue;

    private String reason;

    @PrePersist
    protected void onCreate() {
        this.changedAt = LocalDateTime.now();
    }
}