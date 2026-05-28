package net.ilyasse.proctoringservice.repository;

import net.ilyasse.proctoringservice.entity.FraudEvent;
import net.ilyasse.proctoringservice.enums.FraudEventType;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface FraudEventRepository extends JpaRepository<FraudEvent, UUID> {
    List<FraudEvent> findBySessionIdOrderByDetectedAtDesc(UUID sessionId);
    List<FraudEvent> findByExamId(UUID examId);
    long countBySessionIdAndEventType(UUID sessionId, FraudEventType eventType);
}