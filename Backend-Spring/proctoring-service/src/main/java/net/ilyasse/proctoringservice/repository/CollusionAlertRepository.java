package net.ilyasse.proctoringservice.repository;

import net.ilyasse.proctoringservice.entity.CollusionAlert;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface CollusionAlertRepository extends JpaRepository<CollusionAlert, UUID> {
    List<CollusionAlert> findByExamIdOrderByDetectedAtDesc(UUID examId);
}
