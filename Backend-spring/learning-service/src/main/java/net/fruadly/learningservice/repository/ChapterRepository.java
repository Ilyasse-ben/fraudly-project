package net.fruadly.learningservice.repository;

import net.fruadly.learningservice.entity.Chapter;
import net.fruadly.learningservice.entity.Enrollment;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface ChapterRepository extends JpaRepository<Chapter, UUID> {

}
