package net.fruadly.learningservice.controller;

import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.dto.ChapitrDto;
import net.fruadly.learningservice.service.ChapitreService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/chapitres")
@RequiredArgsConstructor
public class ChapitreController {
    private final ChapitreService chapterService;

    @PostMapping("/{courseId}")
    public ResponseEntity<ChapitrDto> create(@PathVariable UUID courseId, @RequestBody ChapitrDto dto) {
        return new ResponseEntity<>(chapterService.addChapterToCourse(courseId, dto), HttpStatus.CREATED);
    }
    @PutMapping("/{id}")
    public ResponseEntity<ChapitrDto> update(@PathVariable UUID id, @RequestBody ChapitrDto dto) {
        return new ResponseEntity<>(chapterService.updateChapter(id, dto), HttpStatus.CREATED);
    }
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable UUID id) {
        chapterService.deleteChapitre(id);
        return ResponseEntity.noContent().build();
    }
    @GetMapping("/{id}")
    public ResponseEntity<ChapitrDto> getById(@PathVariable UUID id) {
        return ResponseEntity.ok(chapterService.getChapterById(id));
    }

}
