package net.fruadly.learningservice.mapper;

import net.fruadly.learningservice.dto.ChapitrDto;
import net.fruadly.learningservice.entity.Chapter;
import org.springframework.stereotype.Component;

@Component
public class ChapitreMapper {
    // On injecte le ResourceMapper pour transformer les fichiers liés
    //private final ResourceMapper resourceMapper;

    public ChapitrDto toDto(Chapter entity) {
        if (entity == null) return null;

        ChapitrDto dto = new ChapitrDto();
        dto.setId(entity.getId());
        dto.setTitle(entity.getTitle());
        dto.setResources(entity.getResources());
        dto.setDateChapitre(entity.getDateChapitre());


        // Mapping des ressources associées
//        if (entity.getResources() != null) {
//            dto.setResources(entity.getResources().stream()
//                    .map(resourceMapper::toDto)
//                    .collect(Collectors.toList()));
//        }

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
