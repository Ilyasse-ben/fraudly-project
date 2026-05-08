package net.ilyasse.assessmentservice.repository;


import net.ilyasse.assessmentservice.entity.ExamConfig;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
import java.util.UUID;
/**
 * @author ELHAID Yousef
 **/
public interface ExamConfigRepository extends JpaRepository<ExamConfig, UUID> {
    Optional<ExamConfig> findByExamId(UUID examId);
}
