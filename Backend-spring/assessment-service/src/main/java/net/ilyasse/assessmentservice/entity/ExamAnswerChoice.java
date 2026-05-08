package net.ilyasse.assessmentservice.entity;

import jakarta.persistence.*;
import lombok.*;
import java.util.UUID;
/**
 * @author ELHAID Yousef
 **/

@Entity
@Table(name = "exam_answer_choices")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class ExamAnswerChoice {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne
    @JoinColumn(name = "answer_id", nullable = false)
    private ExamAnswer answer;

    @Column(nullable = false)
    private UUID choiceId;
}
