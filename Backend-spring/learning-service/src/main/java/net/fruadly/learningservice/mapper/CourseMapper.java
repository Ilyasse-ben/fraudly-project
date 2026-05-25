package net.fruadly.learningservice.mapper;

import net.fruadly.learningservice.dto.CoursGetDto;
import net.fruadly.learningservice.dto.CoursPostDto;
import net.fruadly.learningservice.entity.Cours;
import org.springframework.stereotype.Component;

import java.util.Date;

@Component
public class CourseMapper {
    public CoursPostDto toPostDto(Cours entity) {
        if (entity == null) return null;
        CoursPostDto dto = new CoursPostDto();
        dto.setTitle(entity.getTitle());
        dto.setDescription(entity.getDescription());
        dto.setCategory(entity.getCategory());
        dto.setId(entity.getId());
        return dto;
    }

    public CoursGetDto toGetDto(Cours entity) {
        if (entity == null) return null;
        CoursGetDto dto = new CoursGetDto();
        dto.setId(entity.getId());
        dto.setTitle(entity.getTitle());
        dto.setDescription(entity.getDescription());
        dto.setCategory(entity.getCategory());
        dto.setProfId(entity.getProfId());
        dto.setChapters(entity.getChapters());
        dto.setEnrollments(entity.getEnrollments());
        dto.setCoursCode(entity.getCoursCode());
        dto.setChapterCount(entity.getChapters() != null ? entity.getChapters().size() : 0);
        return dto;
    }

    public Cours toEntity(CoursPostDto dto) {
        if (dto == null) return null;
        Cours entity = new Cours();
        entity.setTitle(dto.getTitle());
        entity.setDescription(dto.getDescription());
        entity.setCategory(dto.getCategory());
        entity.setCourseDate(new Date());
        return entity;
    }
}