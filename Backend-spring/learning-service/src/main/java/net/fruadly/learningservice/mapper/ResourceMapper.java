package net.fruadly.learningservice.mapper;

import net.fruadly.learningservice.dto.ResourceDto;
import net.fruadly.learningservice.entity.Resource;
import org.springframework.stereotype.Component;

@Component
public class ResourceMapper {
    public ResourceDto toDto(Resource entity) {
        if (entity == null) return null;

        ResourceDto dto = new ResourceDto();
        dto.setId(entity.getId());
        dto.setFileName(entity.getFileName());
        dto.setFileUrl(entity.getFileUrl());
        dto.setMimeType(entity.getMimeType());
        // On ne renvoie pas extractedText ici pour optimiser la bande passante
        return dto;
    }

    public Resource toEntity(ResourceDto dto) {
        if (dto == null) return null;

        Resource entity = new Resource();
        entity.setFileName(dto.getFileName());
        entity.setFileUrl(dto.getFileUrl());
        entity.setMimeType(dto.getMimeType());
        return entity;
    }
}
