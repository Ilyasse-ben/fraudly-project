package net.fruadly.learningservice.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.fruadly.learningservice.dto.AiResultEvent;
import net.fruadly.learningservice.entity.Resource;
import net.fruadly.learningservice.enums.IngestionStatus;
import net.fruadly.learningservice.repository.ResourceRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Locale;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class ResourceIngestionStatusService {

    private final ResourceRepository resourceRepository;

    @Transactional
    public void applyAiResult(AiResultEvent event, String rawMessage) {
        if (event == null || event.getResourceId() == null) {
            log.warn("Ignoring ai_results event without resource_id: {}", rawMessage);
            return;
        }

        final UUID resourceId = event.getResourceId();
        final String normalizedStatus = normalizeStatus(event.getStatus());

        if (normalizedStatus == null) {
            log.warn("Ignoring ai_results with unknown status for resource {}: {}", resourceId, event.getStatus());
            return;
        }

        final Resource resource = resourceRepository.findByIdForUpdate(resourceId)
                .orElse(null);

        if (resource == null) {
            log.warn("Received ai_results for unknown resource {}", resourceId);
            return;
        }

        final IngestionStatus targetStatus = toResourceStatus(normalizedStatus);
        if (targetStatus == null) {
            log.warn("No target status mapping for ai status '{}'", normalizedStatus);
            return;
        }

        final IngestionStatus currentStatus = resource.getIngestionStatus();
        if (isOutOfOrderDowngrade(currentStatus, targetStatus)) {
            log.info(
                    "Ignoring out-of-order ai_results transition for resource {} ({} -> {})",
                    resourceId,
                    currentStatus,
                    targetStatus
            );
            return;
        }

        resource.setIngestionStatus(targetStatus);

        if (event.getChunksIndexed() != null) {
            resource.setChunksIndexed(event.getChunksIndexed());
        }
        if (event.getPagesProcessed() != null) {
            resource.setPagesProcessed(event.getPagesProcessed());
        }
        if (event.getVectorId() != null && !event.getVectorId().isBlank()) {
            resource.setVectorId(event.getVectorId());
        }

        if (targetStatus == IngestionStatus.READY) {
            resource.setIndexedAt(LocalDateTime.now());
            resource.setIngestionError(null);
        } else if (targetStatus == IngestionStatus.FAILED) {
            String error = event.getError();
            if (error == null || error.isBlank()) {
                error = "AI ingestion failed with status: " + normalizedStatus;
            }
            resource.setIngestionError(error);
        }

        resourceRepository.save(resource);

        log.info(
                "Applied ai_results to resource {} -> status={}, chunksIndexed={}, pagesProcessed={}",
                resourceId,
                targetStatus,
                resource.getChunksIndexed(),
                resource.getPagesProcessed()
        );
    }

    private boolean isOutOfOrderDowngrade(IngestionStatus currentStatus, IngestionStatus targetStatus) {
        return currentStatus == IngestionStatus.READY && targetStatus == IngestionStatus.FAILED;
    }

    private IngestionStatus toResourceStatus(String normalizedStatus) {
        return switch (normalizedStatus) {
            case "ok", "empty" -> IngestionStatus.READY;
            case "failed", "error" -> IngestionStatus.FAILED;
            case "processing" -> IngestionStatus.PROCESSING;
            default -> null;
        };
    }

    private String normalizeStatus(String status) {
        if (status == null || status.isBlank()) {
            return null;
        }
        return status.trim().toLowerCase(Locale.ROOT);
    }
}
