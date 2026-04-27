package net.fruadly.learningservice.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.UUID;

@Entity
@Table(name = "resources")

@Getter @Setter @NoArgsConstructor @AllArgsConstructor
public class Resource {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    private String fileName;
    private String fileUrl; // Stockage AWS S3 [cite: 102]
    private String mimeType; // PDF, DOCX, etc. [cite: 76]
    @Column(columnDefinition = "TEXT")
    private String extractedText; // Pour l'IA (OCR) [cite: 76, 79]
    private String vectorId; // Lien vers Pinecone/Weaviate [cite: 79, 102]
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "chapter_id")
    @JsonIgnore
    private Chapter chapter;
}