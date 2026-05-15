package net.fruadly.learningservice.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import net.fruadly.learningservice.enums.IngestionStatus;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "resources")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class Resource {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    private String fileName;

    private String fileUrl;

    private String mimeType;

    @Column(columnDefinition = "TEXT")
    private String extractedText;

    private String vectorId;


    @Enumerated(EnumType.STRING)
    private IngestionStatus ingestionStatus;

    /**
     * IA indexing metadata
     */
    private Integer chunksIndexed;

    private Integer pagesProcessed;

    @Column(columnDefinition = "TEXT")
    private String ingestionError;

    private LocalDateTime indexedAt;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "chapter_id")
    @JsonIgnore
    private Chapter chapter;
}