package net.ilyasse.analyticsservice.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(
        name = "student_learning_profile",
        uniqueConstraints = @UniqueConstraint(columnNames = {"student_id", "course_id"})
)
@Getter @Setter @Builder
@NoArgsConstructor @AllArgsConstructor
public class StudentLearningProfile {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "student_id", nullable = false)
    private UUID studentId;

    @Column(name = "course_id", nullable = false)
    private UUID courseId;

    @Column(name = "completed_chapters_json", columnDefinition = "TEXT", nullable = false)
    private String completedChaptersJson;

    @Column(name = "scores_json", columnDefinition = "TEXT", nullable = false)
    private String scoresJson;

    @Column(name = "weak_topics_json", columnDefinition = "TEXT", nullable = false)
    private String weakTopicsJson;

    @Column(name = "interactions_count", nullable = false)
    private Integer interactionsCount;

    private LocalDateTime lastInteractionAt;

    @CreationTimestamp
    private LocalDateTime createdAt;

    @UpdateTimestamp
    private LocalDateTime updatedAt;
}
