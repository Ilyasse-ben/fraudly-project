package net.fruadly.learningservice.repository;

import net.fruadly.learningservice.entity.Enrollment;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface EnrollmentRepository extends JpaRepository<Enrollment, UUID> {
    public boolean existsBystudentId(UUID id);
}
