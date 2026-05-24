package net.ilyasse.assessmentservice.entity;

import jakarta.persistence.*;
import lombok.*;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/

@Entity
@Table(name = "question_choices")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class QuestionChoice {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne
    @JoinColumn(name = "question_id", nullable = false)
    private ExamQuestion question;

    @Column(nullable = false)
    private String label;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String text;

    @Column(nullable = false)
    private Boolean isCorrect = false;
}