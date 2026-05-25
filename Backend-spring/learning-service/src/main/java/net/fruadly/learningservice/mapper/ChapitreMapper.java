package net.fruadly.learningservice.mapper;

import net.fruadly.learningservice.dto.ChapitrDto;
import net.fruadly.learningservice.entity.Chapter;
import org.springframework.stereotype.Component;

import java.util.ArrayList;

@Component
public class ChapitreMapper {
    // On injecte le ResourceMapper pour transformer les fichiers liés
    //private final ResourceMapper resourceMapper;

    public ChapitrDto toDto(Chapter entity) {
        if (entity == null) return null;
        ChapitrDto dto = new ChapitrDto();
        dto.setId(entity.getId());
        dto.setTitle(entity.getTitle());
        dto.setResources(entity.getResources() != null ? entity.getResources() : new ArrayList<>());
        dto.setDateChapitre(entity.getDateChapitre());
        return dto;
    }

    public Chapter toEntity(ChapitrDto dto) {
        if (dto == null) return null;
        Chapter entity = new Chapter();
        entity.setTitle(dto.getTitle());
        entity.setResources(dto.getResources());
        entity.setDateChapitre(dto.getDateChapitre());
        return entity;
    }
}
