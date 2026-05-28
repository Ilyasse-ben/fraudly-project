package net.ilyasse.proctoringservice.entity;

import jakarta.persistence.*;
import lombok.*;
import net.ilyasse.proctoringservice.enums.SessionStatus;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "proctoring_sessions")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class ProctoringSession {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false)
    private UUID studentId;

    @Column(nullable = false)
    private UUID examId;

    @Column(nullable = false)
    private UUID attemptId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private SessionStatus status;

    @Column(nullable = false)
    private Integer fraudScore;

    private String deviceFingerprint;

    @Column(nullable = false, updatable = false)
    private LocalDateTime startedAt;

    private LocalDateTime endedAt;

    @PrePersist
    void onCreate() {
        if (startedAt == null) startedAt = LocalDateTime.now();
        if (fraudScore == null) fraudScore = 0;
        if (status == null) status = SessionStatus.IN_PROGRESS;
    }
}