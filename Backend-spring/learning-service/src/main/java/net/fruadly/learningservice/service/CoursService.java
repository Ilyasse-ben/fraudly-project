package net.fruadly.learningservice.service;



import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.dto.CoursGetDto;
import net.fruadly.learningservice.dto.CoursPostDto;
import net.fruadly.learningservice.entity.Cours;
import net.fruadly.learningservice.mapper.CourseMapper;
import net.fruadly.learningservice.repository.CoursRepository;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional
public class CoursService {

    private final CoursRepository courseRepository;
    private final CourseMapper courseMapper;

    public CoursPostDto createCourse(CoursPostDto coursPostDto) {
        Cours cours = courseMapper.toEntity(coursPostDto);
        // Logique spécifique : un nouveau cours commence toujours à la version 1
        Cours savedCourse = courseRepository.save(cours);
        return courseMapper.toPostDto(savedCourse);
    }

    public List<CoursGetDto> getAllCourses() {
        return courseRepository.findAll().stream()
                .map(courseMapper::toGetDto)
                .collect(Collectors.toList());
    }
    public CoursGetDto getCourseById(UUID id) {
        Cours cours = courseRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Cours non trouvé avec l'id : " + id));
        return courseMapper.toGetDto(cours);
    }



    public CoursPostDto updateCourse(UUID id, CoursPostDto coursGetDto) {
        // On vérifie d'abord si le cours existe
        Cours existingCourse = courseRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Impossible de mettre à jour : Cours non trouvé"));

        // Mise à jour des champs
        existingCourse.setTitle(coursGetDto.getTitle());
        existingCourse.setDescription(coursGetDto.getDescription());
        existingCourse.setCategory(coursGetDto.getCategory());

        // Note : On ne change généralement pas l'instructorId ou l'ID lors d'un update

        Cours updatedCourse = courseRepository.save(existingCourse);
        return courseMapper.toPostDto(updatedCourse);
    }


    public void deleteCourse(UUID id) {
        if (!courseRepository.existsById(id)) {
            throw new RuntimeException("Impossible de supprimer : Cours non trouvé");
        }
        courseRepository.deleteById(id);
    }

}
