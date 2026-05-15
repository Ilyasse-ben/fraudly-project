package net.fruadly.learningservice.service;

import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.dto.ResourceDto;
import net.fruadly.learningservice.entity.Chapter;
import net.fruadly.learningservice.entity.Resource;
import net.fruadly.learningservice.enums.IngestionStatus;
import net.fruadly.learningservice.mapper.ResourceMapper;
import net.fruadly.learningservice.repository.ChapterRepository;
import net.fruadly.learningservice.repository.ResourceRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetUrlRequest;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class S3Service {

    @Autowired
    private S3Client s3Client;

    @Autowired
    private ResourceRepository resourceRepository;

    @Autowired
    private ResourceMapper resourceMapper;

    @Autowired
    private ChapterRepository chapterRepository;

    @Autowired
    private net.fruadly.learningservice.kafka.ResourceProducer resourceProducer;

    public ResourceDto uplodFile(MultipartFile file, String type, Chapter chapter) {

        Resource resource = new Resource();
        resource.setFileName(file.getOriginalFilename());
        resource.setMimeType(type);
        resource.setChapter(chapter);
        resource.setIngestionStatus(IngestionStatus.PROCESSING);

        Resource saved = resourceRepository.save(resource);

        try {
            String fileName = UUID.randomUUID() + "-" + file.getOriginalFilename();
            byte[] bytes = file.getBytes();

            PutObjectRequest request = PutObjectRequest.builder()
                    .bucket("your-bucket") // garde ton @Value si tu veux
                    .key(fileName)
                    .contentType(file.getContentType())
                    .build();

            s3Client.putObject(request, RequestBody.fromBytes(bytes));

            GetUrlRequest getUrlRequest = GetUrlRequest.builder()
                    .bucket("your-bucket")
                    .key(fileName)
                    .build();

            String urlFile = s3Client.utilities().getUrl(getUrlRequest).toString();

            saved.setFileUrl(urlFile);
            saved.setIngestionStatus(IngestionStatus.PROCESSING);
            resourceRepository.save(saved);

            // 2. Kafka event
            String courseId = chapter.getCours() != null ? chapter.getCours().getId().toString() : null;
            String chapterId = chapter.getId() != null ? chapter.getId().toString() : null;

            resourceProducer.publishResource(
                    resourceMapper.toDto(saved),
                    bytes,
                    courseId,
                    chapterId
            );

            return resourceMapper.toDto(saved);

        } catch (Exception ex) {

            Resource db = resourceRepository.findById(saved.getId())
                    .orElse(saved);

            db.setIngestionStatus(IngestionStatus.FAILED);
            db.setIngestionError(ex.getMessage());

            resourceRepository.save(db);

            throw new RuntimeException("Erreur S3: " + ex.getMessage(), ex);
        }
    }

    public ResourceDto uplodLien(String lien, String type, Chapter chapter) {

        Resource resource = new Resource();
        resource.setFileName(lien);
        resource.setFileUrl(lien);
        resource.setMimeType(type);
        resource.setChapter(chapter);
        resource.setIngestionStatus(IngestionStatus.READY);
        resource.setIndexedAt(LocalDateTime.now());

        Resource saved = resourceRepository.save(resource);

        return resourceMapper.toDto(saved);
    }

    public ResourceDto uploadResource(MultipartFile file, String type, String lien, UUID chapterId)
            throws IOException {

        Chapter chapter = chapterRepository.findById(chapterId)
                .orElseThrow(() -> new RuntimeException("chapitre non trouvé"));

        return type.equals("lien")
                ? uplodLien(lien, type, chapter)
                : uplodFile(file, type, chapter);
    }
}