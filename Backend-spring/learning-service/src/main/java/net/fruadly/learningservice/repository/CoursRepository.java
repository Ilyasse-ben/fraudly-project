package net.fruadly.learningservice.repository;

import net.fruadly.learningservice.entity.Cours;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface CoursRepository extends JpaRepository<Cours, UUID> {
    Cours findByCoursCode(String str);
    Boolean existsByCoursCode(String str);
}
