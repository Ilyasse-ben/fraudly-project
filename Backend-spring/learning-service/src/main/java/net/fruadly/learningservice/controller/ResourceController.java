package net.fruadly.learningservice.controller;

import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.dto.ResourceDto;
import net.fruadly.learningservice.service.FileStorageService;
import net.fruadly.learningservice.service.ResourceService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/resources")
@RequiredArgsConstructor
@Transactional
public class ResourceController {
    private final ResourceService resourceService;

    // Ajouter une ressource (document/vidéo) à un chapitre
    @PostMapping("/{id}")
    public ResponseEntity<ResourceDto> addResource(@PathVariable UUID id, List<MultipartFile> files) {
        files.forEach(file ->{
            new ResponseEntity<>(resourceService.addResourceToChapter(id, file), HttpStatus.CREATED);
        });
        return new ResponseEntity<>( HttpStatus.CREATED);
    }


    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteResource(@PathVariable UUID id) {
        resourceService.deleteResource(id);
        return ResponseEntity.noContent().build();
    }
}
