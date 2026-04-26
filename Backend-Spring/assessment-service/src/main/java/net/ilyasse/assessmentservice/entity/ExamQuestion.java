package net.ilyasse.assessmentservice.entity;


import jakarta.persistence.*;
import lombok.*;
import net.ilyasse.assessmentservice.enums.Difficulty;
import net.ilyasse.assessmentservice.enums.QuestionType;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/

@Entity
@Table(name = "exam_questions")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class ExamQuestion {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne
    @JoinColumn(name = "exam_id", nullable = false)
    private Exam exam;

    @Column(nullable = false)
    private Integer orderIndex;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private QuestionType type;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String questionText;

    @Column(columnDefinition = "TEXT")
    private String correctAnswer;

    @Column(columnDefinition = "TEXT")
    private String explanation;

    @Column(nullable = false)
    private Integer points = 1;

    @Enumerated(EnumType.STRING)
    private Difficulty difficulty;

    @Column(nullable = false)
    private Boolean generatedByAi = false;

    @Column(nullable = false)
    private Boolean editedByTeacher = false;

    @Column(columnDefinition = "TEXT")
    private String originalText;

    @Column(columnDefinition = "TEXT")
    private String finalText;
}
