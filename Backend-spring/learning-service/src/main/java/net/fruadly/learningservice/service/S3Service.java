package net.fruadly.learningservice.service;

import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.dto.ResourceDto;
import net.fruadly.learningservice.entity.Chapter;
import net.fruadly.learningservice.entity.Cours;
import net.fruadly.learningservice.entity.Resource;
import net.fruadly.learningservice.mapper.ResourceMapper;
import net.fruadly.learningservice.repository.ChapterRepository;
import net.fruadly.learningservice.repository.ResourceRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import software.amazon.awssdk.auth.credentials.AwsSessionCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetUrlRequest;
import software.amazon.awssdk.services.s3.model.ListObjectsV2Request;
import software.amazon.awssdk.services.s3.model.ListObjectsV2Response;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

import java.io.IOException;
import java.net.URI;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class S3Service {
    @Value("${aws.bucketName}")
    private String bucketName;
    @Value("${aws.region}")
    private String region;
    @Value("${aws.accessKey}")
    private String accessKey;

    @Value("${aws.secretKey}")
    private String secretKey;
    @Value("${aws.sessionToken}")
    private String sessionToken;
    @Autowired
    private S3Client s3Client;
    @Autowired
    private ResourceRepository resourceRepository;
    @Autowired
    private ResourceMapper resourceMapper;
    @Autowired
    private ChapterRepository chapterRepository;

    // la méthode qui uplode le ficher en cloude
    public ResourceDto uplodFile(MultipartFile file,String type, Chapter chapter){
        try {

            Resource resource=new Resource();
            String fileName = UUID.randomUUID() + "-" + file.getOriginalFilename();
            PutObjectRequest request = PutObjectRequest.builder()
                    .bucket(bucketName)
                    .key(fileName)
                    .contentType(file.getContentType())
                    .build();
            s3Client.putObject(request, RequestBody.fromBytes(file.getBytes()));
            // Utilise l'utilitaire AWS pour récupérer l'URL propre
            GetUrlRequest getUrlRequest = GetUrlRequest.builder()
                    .bucket(bucketName)
                    .key(fileName)
                    .build();
            String urlFile=s3Client.utilities().getUrl(getUrlRequest).toString();
            resource.setFileName(file.getOriginalFilename());
            resource.setFileUrl(urlFile);
            resource.setMimeType(type);
            resource.setChapter(chapter);
            return resourceMapper.toDto(resourceRepository.save(resource));
        } catch (Exception e) {
            throw new RuntimeException("Erreur S3: " + e.getMessage(), e);
        }
    }
    // cette méthode permet de stoker le lein
    public ResourceDto uplodLien(String lien,String type, Chapter chapter){
        try {

            Resource resource=new Resource();
            resource.setFileName(lien);
            resource.setFileUrl(lien);
            resource.setMimeType(type);
            resource.setChapter(chapter);
            return resourceMapper.toDto(resourceRepository.save(resource));
        } catch (Exception e) {
            throw new RuntimeException("Erreur " + e.getMessage(), e);
        }
    }

    public ResourceDto uploadResource(MultipartFile file,String type,String lien, UUID chapterId) throws IOException {

            Chapter chapter = chapterRepository.findById(chapterId).orElseThrow(() -> new RuntimeException("chapitre non trouvé"));

            return type.equals("lien")?this.uplodLien(lien,type,chapter): this.uplodFile(file,type,chapter);
    }


}
