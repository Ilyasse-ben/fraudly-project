package net.ilyasse.proctoringservice.entity;

import jakarta.persistence.*;
import lombok.*;
import net.ilyasse.proctoringservice.enums.FraudEventType;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "fraud_events")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class FraudEvent {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false)
    private UUID sessionId;

    @Column(nullable = false)
    private UUID studentId;

    @Column(nullable = false)
    private UUID examId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private FraudEventType eventType;

    @Column(nullable = false)
    private Double confidenceScore;

    @Column(columnDefinition = "TEXT")
    private String details;

    @Column(nullable = false)
    private LocalDateTime detectedAt;

    @PrePersist
    void onCreate() {
        if (detectedAt == null) detectedAt = LocalDateTime.now();
    }
}