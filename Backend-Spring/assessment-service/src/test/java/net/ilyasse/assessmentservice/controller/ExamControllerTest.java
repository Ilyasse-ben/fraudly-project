package net.ilyasse.assessmentservice.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import net.ilyasse.assessmentservice.dto.request.ExamConfigRequest;
import net.ilyasse.assessmentservice.dto.response.ExamResponse;
import net.ilyasse.assessmentservice.enums.Difficulty;
import net.ilyasse.assessmentservice.enums.ExamStatus;
import net.ilyasse.assessmentservice.enums.QuestionType;
import net.ilyasse.assessmentservice.service.ExamAttemptService;
import net.ilyasse.assessmentservice.service.ExamService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ExamController.class)
class ExamControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private ExamService examService;

    @MockBean
    private ExamAttemptService examAttemptService;

    @Test
    void createExam_usesRealChapterFixtureAndReturnsExamPayload() throws Exception {
        JsonNode chapterFixture = loadChapterFixture();
        UUID courseId = UUID.fromString(chapterFixture.get("course_id").asText());
        UUID chapterId = UUID.fromString(chapterFixture.get("chapter_id").asText());
        UUID professorId = UUID.fromString("8f1d5c4a-9bde-4b8d-8b9d-5d5d93f2a101");

        ExamResponse response = ExamResponse.builder()
                .id(UUID.fromString("9a0d6c52-4f6d-4d6b-9b56-3c3e1d4b8f01"))
            .title("Examen - Fraude documentaire")
            .topic("Fraude documentaire")
                .difficulty(Difficulty.MEDIUM)
                .status(ExamStatus.DRAFT)
                .version(1)
                .courseId(courseId)
                .professorId(professorId)
                .durationMinutes(45)
                .createdAt(LocalDateTime.of(2026, 4, 26, 10, 0))
                .questions(List.of())
                .build();

        when(examService.createExam(any(ExamConfigRequest.class))).thenReturn(response);

        String requestJson = """
                {
                  "topic": "Fraude documentaire",
                  "courseId": "%s",
                  "professorId": "%s",
                  "title": "Examen - Fraude documentaire",
                  "durationMinutes": 45,
                  "nbQcm": 1,
                  "qcmType": "QCM_SINGLE",
                  "nbTrueFalse": 1,
                  "nbOpen": 1,
                  "chapterIds": ["%s"],
                  "difficulty": "MEDIUM",
                  "topK": 2,
                  "includeExplanations": true,
                  "professorInstructions": "Utilise le chapitre de test pour les indices techniques."
                }
                """.formatted(courseId, professorId, chapterId);

        mockMvc.perform(post("/api/exams/generate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(requestJson))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value("Examen - Fraude documentaire"))
                .andExpect(jsonPath("$.topic").value("Fraude documentaire"))
                .andExpect(jsonPath("$.status").value("DRAFT"))
                .andExpect(jsonPath("$.courseId").value(courseId.toString()))
                .andExpect(jsonPath("$.professorId").value(professorId.toString()))
                .andExpect(jsonPath("$.questions").isArray())
                .andExpect(jsonPath("$.questions.length()").value(0));

        var requestCaptor = org.mockito.ArgumentCaptor.forClass(ExamConfigRequest.class);
        verify(examService, times(1)).createExam(requestCaptor.capture());

        ExamConfigRequest captured = requestCaptor.getValue();
        assertThat(captured.getCourseId()).isEqualTo(courseId);
        assertThat(captured.getChapterIds()).containsExactly(chapterId);
        assertThat(captured.getQcmType()).isEqualTo(QuestionType.QCM_SINGLE);
        assertThat(captured.getDifficulty()).isEqualTo(Difficulty.MEDIUM);
        assertThat(captured.getProfessorInstructions()).contains("chapitre de test");
    }

    private JsonNode loadChapterFixture() throws IOException {
        return objectMapper.readTree(new ClassPathResource("fixtures/assessment_real_chapter.json").getInputStream());
    }
}