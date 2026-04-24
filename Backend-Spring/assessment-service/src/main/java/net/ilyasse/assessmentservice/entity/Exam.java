package net.ilyasse.assessmentservice.entity;

import jakarta.persistence.*;
import lombok.*;
import net.ilyasse.assessmentservice.enums.Difficulty;
import net.ilyasse.assessmentservice.enums.ExamStatus;
import java.time.LocalDateTime;


/**
 * @author ELHAID Yousef
 **/

@Entity
@Table(name = "exams")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class Exam {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String title;

    private String topic;

    @Enumerated(EnumType.STRING)
    private Difficulty difficulty;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private ExamStatus status;

    @Column(nullable = false)
    private Integer version = 1;

    @Column(nullable = false)
    private Long courseId;

    @Column(nullable = false)
    private Long professorId;

    private Integer durationMinutes;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    private LocalDateTime publishedAt;
    private LocalDateTime startDate;
    private LocalDateTime endDate;

    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
        if (this.status == null) this.status = ExamStatus.DRAFT;
        if (this.version == null) this.version = 1;
    }
}