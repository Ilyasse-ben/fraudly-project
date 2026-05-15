package net.fruadly.learningservice.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.UUID;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class AiResultEvent {

    @JsonProperty("resource_id")
    private UUID resourceId;

    private String status;

    @JsonProperty("chunks_indexed")
    private Integer chunksIndexed;

    @JsonProperty("pages_processed")
    private Integer pagesProcessed;

    @JsonProperty("ingestion_error")
    private String error;

    @JsonProperty("vector_id")
    private String vectorId;
}