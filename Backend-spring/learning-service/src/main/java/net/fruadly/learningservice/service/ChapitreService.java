package net.fruadly.learningservice.service;


import lombok.Data;
import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.dto.ChapitrDto;
import net.fruadly.learningservice.entity.Chapter;
import net.fruadly.learningservice.entity.Cours;
import net.fruadly.learningservice.mapper.ChapitreMapper;
import net.fruadly.learningservice.repository.ChapterRepository;
import net.fruadly.learningservice.repository.CoursRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ChapitreService {

    private final ChapterRepository chapterRepository;
    private final CoursRepository courseRepository;
    private final ChapitreMapper chapitreMapper ;

    @Transactional
    public ChapitrDto addChapterToCourse(UUID courseId, ChapitrDto dto) {
        Cours cours = courseRepository.findById(courseId)
                .orElseThrow(() -> new RuntimeException("Cours non trouvé"));
        Chapter chapter = chapitreMapper.toEntity(dto);
        chapter.setDateChapitre(new Date());
        chapter.setCours(cours);

        return chapitreMapper.toDto(chapterRepository.save(chapter));
    }
    @Transactional
    public ChapitrDto updateChapter(UUID chapitreId, ChapitrDto dto) {
        Chapter chapter = chapterRepository.findById(chapitreId)
                .orElseThrow(() -> new RuntimeException("chapitr non trouvé méthode put"));
        chapter.setDateChapitre(new Date());
        chapter.setTitle(dto.getTitle());
        return chapitreMapper.toDto(chapterRepository.save(chapter));
    }

    @Transactional
    public void deleteChapitre(UUID id) {
        chapterRepository.deleteById(id);
    }
    @Transactional(readOnly = true)
    public ChapitrDto getChapterById(UUID id) {
        return chapterRepository.findById(id)
                .map(chapitreMapper::toDto)
                .orElseThrow(() -> new RuntimeException("Chapitre non trouvé"));
    }
}
