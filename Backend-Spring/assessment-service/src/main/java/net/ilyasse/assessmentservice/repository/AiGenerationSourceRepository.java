package net.ilyasse.assessmentservice.repository;

import net.ilyasse.assessmentservice.entity.AiGenerationSource;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/
public interface AiGenerationSourceRepository extends JpaRepository<AiGenerationSource, UUID> {
    List<AiGenerationSource> findByExamId(UUID examId);
    List<AiGenerationSource> findByExamIdAndIsRagContext(UUID examId, Boolean isRagContext);
}