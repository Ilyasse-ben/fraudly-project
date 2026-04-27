package net.fruadly.learningservice.service;

import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.dto.ResourceDto;
import net.fruadly.learningservice.entity.Chapter;
import net.fruadly.learningservice.entity.Resource;
import net.fruadly.learningservice.mapper.ResourceMapper;
import net.fruadly.learningservice.repository.ChapterRepository;
import net.fruadly.learningservice.repository.ResourceRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.util.UUID;

@Transactional
@Service
@RequiredArgsConstructor
public class ResourceService {
    @Autowired
    private ResourceRepository resourceRepository;
    @Autowired
    private ChapterRepository chapterRepository ;
    @Autowired
    private ResourceMapper resourceMapper;
    @Autowired
    private FileStorageService fileStorageService;

    @Transactional
    public ResourceDto addResourceToChapter(UUID chapterId, MultipartFile file) {
        Chapter chapter = chapterRepository.findById(chapterId)
                .orElseThrow(() -> new RuntimeException("Chapitre non trouvé"));
        ResourceDto dto=new ResourceDto();
        String originalName = file.getOriginalFilename();
        dto.setFileName(originalName.substring(0, originalName.lastIndexOf(".")));
        String filePath = fileStorageService.save(file);
        dto.setFileUrl(filePath);

        Resource resource = resourceMapper.toEntity(dto);
        resource.setChapter(chapter);



        return resourceMapper.toDto(resourceRepository.save(resource));
    }


    @Transactional
    public void deleteResource(UUID id) {
        resourceRepository.deleteById(id);
    }
}
