package net.ilyasse.analyticsservice.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(
        name = "topic_frequency",
        uniqueConstraints = @UniqueConstraint(columnNames = {"student_id", "course_id", "topic"})
)
@Getter @Setter @Builder
@NoArgsConstructor @AllArgsConstructor

public class TopicFrequency {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "student_id", nullable = false)
    private UUID studentId;

    @Column(name = "course_id")
    private UUID courseId;

    @Column(nullable = false)
    private String topic;

    @Column(nullable = false)
    private Integer count = 1;

    private LocalDateTime lastAskedAt;
}
