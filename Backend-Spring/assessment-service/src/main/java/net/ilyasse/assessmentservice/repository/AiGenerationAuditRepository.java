package net.ilyasse.assessmentservice.repository;

import net.ilyasse.assessmentservice.entity.AiGenerationAudit;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
import java.util.UUID;
/**
 * @author ELHAID Yousef
 **/
public interface AiGenerationAuditRepository extends JpaRepository<AiGenerationAudit, UUID> {
    Optional<AiGenerationAudit> findByExamId(UUID examId);
}