package net.ilyasse.proctoringservice.repository;

import net.ilyasse.proctoringservice.entity.ProctoringSession;
import net.ilyasse.proctoringservice.enums.SessionStatus;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface ProctoringSessionRepository extends JpaRepository<ProctoringSession, UUID> {
    Optional<ProctoringSession> findByAttemptId(UUID attemptId);
    List<ProctoringSession> findByStudentId(UUID studentId);
    List<ProctoringSession> findByExamId(UUID examId);
    List<ProctoringSession> findByStatus(SessionStatus status);
}