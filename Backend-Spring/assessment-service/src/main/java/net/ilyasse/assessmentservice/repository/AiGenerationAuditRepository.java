package net.ilyasse.assessmentservice.repository;

import net.ilyasse.assessmentservice.entity.AiGenerationAudit;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
/**
 * @author ELHAID Yousef
 **/
public interface AiGenerationAuditRepository extends JpaRepository<AiGenerationAudit, Long> {
    Optional<AiGenerationAudit> findByExamId(Long examId);
}