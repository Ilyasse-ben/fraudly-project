package net.ilyasse.assessmentservice.repository;

import net.ilyasse.assessmentservice.entity.AiGenerationSource;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

/**
 * @author ELHAID Yousef
 **/
public interface AiGenerationSourceRepository extends JpaRepository<AiGenerationSource, Long> {
    List<AiGenerationSource> findByExamId(Long examId);
    List<AiGenerationSource> findByExamIdAndIsRagContext(Long examId, Boolean isRagContext);
}