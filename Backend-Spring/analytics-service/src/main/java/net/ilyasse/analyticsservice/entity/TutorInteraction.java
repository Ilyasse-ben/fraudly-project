package net.ilyasse.analyticsservice.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "tutor_interactions")
@Getter @Setter @Builder
@NoArgsConstructor @AllArgsConstructor

public class TutorInteraction {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false)
    private UUID studentId;

    private UUID courseId;
    private UUID chapterId;

    @Column(nullable = false)
    private String sessionId;

    @Column(columnDefinition = "TEXT", nullable = false)
    private String question;

    private String topic;

    private String provider;
    private Boolean fallbackUsed;
    private Integer chunksUsed;

    @CreationTimestamp
    private LocalDateTime askedAt;
}

