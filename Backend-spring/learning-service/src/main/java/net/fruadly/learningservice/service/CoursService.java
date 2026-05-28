package net.fruadly.learningservice.service;

import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.dto.CoursGetDto;
import net.fruadly.learningservice.dto.CoursPostDto;
import net.fruadly.learningservice.entity.Cours;
import net.fruadly.learningservice.mapper.CourseMapper;
import net.fruadly.learningservice.repository.CoursRepository;
import net.fruadly.learningservice.security.SecurityPrincipalUtils;
import org.springframework.stereotype.Service;

import java.security.SecureRandom;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional
public class CoursService {

    private final CoursRepository courseRepository;
    private final CourseMapper courseMapper;
    private final SecurityPrincipalUtils securityPrincipalUtils;

    private String generate(int length) {
        final String CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        final SecureRandom RANDOM = new SecureRandom();
        String token;
        do {
            StringBuilder sb = new StringBuilder(length);
            for (int i = 0; i < length; i++) {
                sb.append(CHARACTERS.charAt(RANDOM.nextInt(CHARACTERS.length())));
            }
            token = sb.toString();
        } while (courseRepository.existsByCoursCode(token));
        return token;
    }

    public CoursPostDto createCourse(CoursPostDto coursPostDto) {
        Cours cours = new Cours();
        cours.setTitle(coursPostDto.getTitle());
        cours.setDescription(coursPostDto.getDescription());
        cours.setCategory(coursPostDto.getCategory());
        cours.setCoursCode(generate(8));
        cours.setProfId(securityPrincipalUtils.requireUserId());

        Cours savedCourse = courseRepository.save(cours);

        return courseMapper.toPostDto(savedCourse);
    }

    public List<CoursGetDto> getAllCourses() {
        return courseRepository.findAll().stream()
                .map(courseMapper::toGetDto)
                .collect(Collectors.toList());
    }

    public CoursGetDto getCourseById(UUID id) {
        return courseRepository.findById(id)
                .map(courseMapper::toGetDto)
                .orElseThrow(() -> new RuntimeException("Cours non trouvé avec l'id : " + id));
    }

    public CoursPostDto updateCourse(UUID id, CoursPostDto dto) {
        Cours existingCourse = courseRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Impossible de mettre à jour : Cours non trouvé"));

        existingCourse.setTitle(dto.getTitle());
        existingCourse.setDescription(dto.getDescription());
        existingCourse.setCategory(dto.getCategory());

        return courseMapper.toPostDto(courseRepository.save(existingCourse));
    }

    public void deleteCourse(UUID id) {
        if (!courseRepository.existsById(id)) {
            throw new RuntimeException("Impossible de supprimer : Cours non trouvé");
        }
        courseRepository.deleteById(id);
    }
}