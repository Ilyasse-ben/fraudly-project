package net.ilyasse.assessmentservice.repository;


import net.ilyasse.assessmentservice.entity.ExamConfig;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
/**
 * @author ELHAID Yousef
 **/
public interface ExamConfigRepository extends JpaRepository<ExamConfig, Long> {
    Optional<ExamConfig> findByExamId(Long examId);
}
