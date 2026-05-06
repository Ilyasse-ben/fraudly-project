package net.fruadly.learningservice.dto;

import jakarta.persistence.*;
import lombok.Data;
import net.fruadly.learningservice.entity.Chapter;

import java.util.UUID;

@Data
public class ResourceDto {
    private UUID id;
    private String fileName;
    private String fileUrl; // Stockage AWS S3 [cite: 102]
    private String mimeType; // PDF, DOCX, etc. [cite: 76]
}
