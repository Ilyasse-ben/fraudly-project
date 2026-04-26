package net.ilyasse.assessmentservice.service.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.ilyasse.assessmentservice.dto.request.BackendAiGenerationRequest;
import net.ilyasse.assessmentservice.dto.response.AiGenerationResponse;
import net.ilyasse.assessmentservice.dto.request.ExamConfigRequest;
import net.ilyasse.assessmentservice.dto.request.UpdateChoiceRequest;
import net.ilyasse.assessmentservice.dto.request.UpdateQuestionRequest;
import net.ilyasse.assessmentservice.dto.response.ExamQuestionResponse;
import net.ilyasse.assessmentservice.dto.response.ExamResponse;
import net.ilyasse.assessmentservice.dto.response.QuestionChoiceResponse;
import net.ilyasse.assessmentservice.entity.*;
import net.ilyasse.assessmentservice.enums.Difficulty;
import net.ilyasse.assessmentservice.enums.ExamStatus;
import net.ilyasse.assessmentservice.enums.QuestionType;
import net.ilyasse.assessmentservice.kafka.CorrectionKafkaProducer;
import net.ilyasse.assessmentservice.repository.*;
import net.ilyasse.assessmentservice.service.ExamService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * @author ELHAID Yousef
 **/
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class ExamServiceImpl implements ExamService {

    private final ExamRepository examRepository;
    private final ExamConfigRepository examConfigRepository;
    private final ExamQuestionRepository examQuestionRepository;
    private final QuestionChoiceRepository questionChoiceRepository;
    private final QuestionRevisionRepository questionRevisionRepository;
    private final AiGenerationSourceRepository aiGenerationSourceRepository;
    private final AiGenerationAuditRepository aiGenerationAuditRepository;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final CorrectionKafkaProducer correctionKafkaProducer;
    private final ExamAttemptRepository examAttemptRepository;
    private final ExamAnswerRepository examAnswerRepository;

    @Value("${ai.service.url}")
    private String aiServiceUrl;

    @Override
    public ExamResponse createExam(ExamConfigRequest request) {
        // 1. Create Exam
        Exam exam = Exam.builder()
                .title(request.getTitle())
                .courseId(request.getCourseId())
                .professorId(request.getProfessorId())
                .durationMinutes(request.getDurationMinutes())
                .difficulty(request.getDifficulty())
                .status(ExamStatus.DRAFT)
                .version(1)
                .build();
        exam = examRepository.save(exam);

        // 2. Save ExamConfig
        ExamConfig config = ExamConfig.builder()
                .exam(exam)
                .nbQcm(request.getNbQcm())
                .qcmType(request.getQcmType())
                .nbTrueFalse(request.getNbTrueFalse())
                .nbOpen(request.getNbOpen())
                .chapterIds(request.getChapterIds().toString())
                .difficulty(request.getDifficulty())
                .configStatus("PENDING")
                .build();
        examConfigRepository.save(config);

        // 3. Call AI service
        AiGenerationResponse aiResponse = callAiService(request);

        // 4. Parse and save questions
        saveQuestionsFromAiResponse(exam, aiResponse, request.getQcmType());

        // 5. Save sources and audit
        saveSourcesFromAiResponse(exam, aiResponse);
        saveAuditFromAiResponse(exam, aiResponse);

        // 6. Update config status
        config.setConfigStatus("GENERATED");
        examConfigRepository.save(config);

        // 7. Update exam topic from AI response
        exam.setTopic(aiResponse.getTopic());
        examRepository.save(exam);

        return getExamById(exam.getId());
    }

    private AiGenerationResponse callAiService(ExamConfigRequest request) {
        try {
            String url = aiServiceUrl + "/generate";
            BackendAiGenerationRequest aiRequest = BackendAiGenerationRequest.builder()
                .topic(request.getTopic() != null && !request.getTopic().isBlank()
                    ? request.getTopic()
                    : request.getTitle())
                .courseId(request.getCourseId() != null ? request.getCourseId().toString() : null)
                .chapterIds(request.getChapterIds() == null ? null : request.getChapterIds().stream()
                    .map(String::valueOf)
                    .toList())
                    .difficulty(mapBackendDifficulty(request.getDifficulty()))
                .totalQuestions(request.getNbQcm() + request.getNbTrueFalse() + request.getNbOpen())
                .qcmCount(request.getNbQcm())
                .trueFalseCount(request.getNbTrueFalse())
                .openCount(request.getNbOpen())
                .includeExplanations(request.getIncludeExplanations() == null || request.getIncludeExplanations())
                .professorInstructions(request.getProfessorInstructions())
                .topK(request.getTopK() != null ? request.getTopK() : 8)
                .build();

            String response = restTemplate.postForObject(url, aiRequest, String.class);
            return objectMapper.readValue(response, AiGenerationResponse.class);
        } catch (Exception e) {
            throw new RuntimeException("Failed to call AI service: " + e.getMessage());
        }
    }

    private void saveQuestionsFromAiResponse(Exam exam, AiGenerationResponse aiResponse, QuestionType qcmType) {
        if (aiResponse.getQuestions() == null) return;

        int index = 1;
        for (AiGenerationResponse.AiQuestion aiQuestion : aiResponse.getQuestions()) {
            QuestionType type = mapQuestionType(aiQuestion.getType(), qcmType);
            int points = 1;
            if (aiQuestion.getMaxScore() != null && aiQuestion.getMaxScore() > 0) {
                points = Math.max(1, (int) Math.ceil(aiQuestion.getMaxScore()));
            }

            ExamQuestion question = ExamQuestion.builder()
                    .exam(exam)
                    .orderIndex(index++)
                    .type(type)
                    .questionText(aiQuestion.getQuestion())
                    .originalText(aiQuestion.getQuestion())
                    .finalText(aiQuestion.getQuestion())
                    .correctAnswer(aiQuestion.getCorrectAnswer())
                    .explanation(aiQuestion.getExplanation())
                    .difficulty(mapDifficulty(aiQuestion.getDifficulty()))
                    .points(points)
                    .generatedByAi(true)
                    .editedByTeacher(false)
                    .build();
            question = examQuestionRepository.save(question);

            // Save choices
            if (aiQuestion.getChoices() != null) {
                for (AiGenerationResponse.AiChoice aiChoice : aiQuestion.getChoices()) {
                    QuestionChoice choice = QuestionChoice.builder()
                            .question(question)
                            .label(aiChoice.getLabel())
                            .text(aiChoice.getText())
                            .isCorrect(aiChoice.getIsCorrect())
                            .build();
                    questionChoiceRepository.save(choice);
                }
            }
        }
    }

    private void saveSourcesFromAiResponse(Exam exam, AiGenerationResponse aiResponse) {
        if (aiResponse.getSources() != null) {
            for (AiGenerationResponse.AiSource source : aiResponse.getSources()) {
                AiGenerationSource s = AiGenerationSource.builder()
                        .exam(exam)
                        .sourceFile(source.getSourceFile())
                        .page(source.getPage())
                        .score(source.getScore())
                        .isRagContext(false)
                        .build();
                aiGenerationSourceRepository.save(s);
            }
        }
        if (aiResponse.getRagContext() != null) {
            for (AiGenerationResponse.AiRagContext rag : aiResponse.getRagContext()) {
                AiGenerationSource s = AiGenerationSource.builder()
                        .exam(exam)
                        .sourceFile(rag.getSourceFile())
                        .page(rag.getPage())
                        .score(rag.getScore())
                        .excerpt(rag.getExcerpt())
                        .isRagContext(true)
                        .build();
                aiGenerationSourceRepository.save(s);
            }
        }
    }

    private void saveAuditFromAiResponse(Exam exam, AiGenerationResponse aiResponse) {
        if (aiResponse.getAudit() == null) return;
        AiGenerationResponse.AiAudit audit = aiResponse.getAudit();
        AiGenerationAudit entity = AiGenerationAudit.builder()
                .exam(exam)
                .provider(audit.getProvider())
                .fallbackUsed(audit.getFallbackUsed())
                .retrievedChunks(audit.getRetrievedChunks())
                .promptChars(audit.getPromptChars())
                .generatedQuestions(audit.getGeneratedQuestions())
                .requestedDifficulty(audit.getRequestedDifficulty())
                .build();
        aiGenerationAuditRepository.save(entity);
    }

    private QuestionType mapQuestionType(String type, QuestionType qcmType) {
        return switch (type.toLowerCase()) {
            case "qcm" -> qcmType != null ? qcmType : QuestionType.QCM_SINGLE;
            case "vrai_faux" -> QuestionType.TRUE_FALSE;
            case "ouverte" -> QuestionType.OPEN;
            default -> QuestionType.QCM_SINGLE;
        };
    }

    private Difficulty mapDifficulty(String difficulty) {
        if (difficulty == null) return Difficulty.MEDIUM;
        return switch (difficulty.toLowerCase()) {
            case "facile" -> Difficulty.EASY;
            case "moyen", "moyenne" -> Difficulty.MEDIUM;
            case "difficile" -> Difficulty.HARD;
            case "tres difficile", "très difficile" -> Difficulty.VERY_HARD;
            default -> Difficulty.MEDIUM;
        };
    }

    private String mapBackendDifficulty(Difficulty difficulty) {
        if (difficulty == null) return "moyen";

        return switch (difficulty) {
            case EASY -> "facile";
            case MEDIUM -> "moyen";
            case HARD, VERY_HARD -> "difficile";
        };
    }

    @Override
    public ExamResponse getExamById(UUID examId) {
        Exam exam = examRepository.findById(examId)
                .orElseThrow(() -> new RuntimeException("Exam not found: " + examId));

        List<ExamQuestion> questions = examQuestionRepository.findByExamIdOrderByOrderIndex(examId);

        List<ExamQuestionResponse> questionResponses = questions.stream().map(q -> {
            List<QuestionChoiceResponse> choices = questionChoiceRepository.findByQuestionId(q.getId())
                    .stream().map(c -> QuestionChoiceResponse.builder()
                            .id(c.getId())
                            .label(c.getLabel())
                            .text(c.getText())
                            .isCorrect(c.getIsCorrect())
                            .build())
                    .collect(Collectors.toList());

            return ExamQuestionResponse.builder()
                    .id(q.getId())
                    .orderIndex(q.getOrderIndex())
                    .type(q.getType())
                    .questionText(q.getQuestionText())
                    .correctAnswer(q.getCorrectAnswer())
                    .explanation(q.getExplanation())
                    .points(q.getPoints())
                    .difficulty(q.getDifficulty())
                    .generatedByAi(q.getGeneratedByAi())
                    .editedByTeacher(q.getEditedByTeacher())
                    .choices(choices)
                    .build();
        }).collect(Collectors.toList());

        return ExamResponse.builder()
                .id(exam.getId())
                .title(exam.getTitle())
                .topic(exam.getTopic())
                .difficulty(exam.getDifficulty())
                .status(exam.getStatus())
                .version(exam.getVersion())
                .courseId(exam.getCourseId())
                .professorId(exam.getProfessorId())
                .durationMinutes(exam.getDurationMinutes())
                .createdAt(exam.getCreatedAt())
                .publishedAt(exam.getPublishedAt())
                .startDate(exam.getStartDate())
                .endDate(exam.getEndDate())
                .questions(questionResponses)
                .build();
    }

    @Override
    public List<ExamResponse> getExamsByProfessor(UUID professorId) {
        return examRepository.findByProfessorId(professorId)
                .stream().map(e -> getExamById(e.getId()))
                .collect(Collectors.toList());
    }

    @Override
    public List<ExamResponse> getExamsByCourse(UUID courseId) {
        return examRepository.findByCourseId(courseId)
                .stream().map(e -> getExamById(e.getId()))
                .collect(Collectors.toList());
    }

    @Override
    public ExamResponse updateQuestion(UUID questionId, UpdateQuestionRequest request, UUID professorId) {
        ExamQuestion question = examQuestionRepository.findById(questionId)
                .orElseThrow(() -> new RuntimeException("Question not found: " + questionId));

        // Save revision before updating
        if (request.getReason() != null) {
            QuestionRevision revision = QuestionRevision.builder()
                    .question(question)
                    .changedBy(professorId)
                    .fieldChanged("questionText")
                    .oldValue(question.getQuestionText())
                    .newValue(request.getQuestionText())
                    .reason(request.getReason())
                    .build();
            questionRevisionRepository.save(revision);
        }

        // Update question
        question.setQuestionText(request.getQuestionText());
        question.setFinalText(request.getQuestionText());
        question.setEditedByTeacher(true);
        if (request.getCorrectAnswer() != null) question.setCorrectAnswer(request.getCorrectAnswer());
        if (request.getExplanation() != null) question.setExplanation(request.getExplanation());
        if (request.getPoints() != null) question.setPoints(request.getPoints());
        examQuestionRepository.save(question);

        // Update choices if provided
        if (request.getChoices() != null) {
            for (UpdateChoiceRequest choiceReq : request.getChoices()) {
                if (choiceReq.getId() != null) {
                    questionChoiceRepository.findById(choiceReq.getId()).ifPresent(choice -> {
                        if (choiceReq.getText() != null) choice.setText(choiceReq.getText());
                        if (choiceReq.getIsCorrect() != null) choice.setIsCorrect(choiceReq.getIsCorrect());
                        questionChoiceRepository.save(choice);
                    });
                }
            }
        }

        return getExamById(question.getExam().getId());
    }

    @Override
    public ExamResponse deleteQuestion(UUID questionId, UUID examId) {
        questionChoiceRepository.deleteByQuestionId(questionId);
        examQuestionRepository.deleteById(questionId);
        return getExamById(examId);
    }

    @Override
    public ExamResponse validateExam(UUID examId) {
        Exam exam = examRepository.findById(examId)
                .orElseThrow(() -> new RuntimeException("Exam not found: " + examId));
        exam.setStatus(ExamStatus.REVIEWED);
        examRepository.save(exam);
        return getExamById(examId);
    }

    @Override
    public ExamResponse publishExam(UUID examId) {
        Exam exam = examRepository.findById(examId)
                .orElseThrow(() -> new RuntimeException("Exam not found: " + examId));
        exam.setStatus(ExamStatus.PUBLISHED);
        examRepository.save(exam);
        return getExamById(examId);
    }
    @Override
    public void launchCorrection(UUID examId, UUID professorId) {
    Exam exam = examRepository.findById(examId)
        .orElseThrow(() -> new RuntimeException("Exam not found: " + examId));
    
    exam.setStatus(ExamStatus.GRADING);
    examRepository.save(exam);
    
    correctionKafkaProducer.publishCorrectionRequested(examId, professorId);
    
    log.info("[Correction] Lancée: exam={} prof={}", examId, professorId);
}
    @Override
    public List<Map<String, Object>> getOpenAnswers(UUID examId) {
        List<ExamAttempt> attempts = examAttemptRepository.findByExamId(examId);
        List<Map<String, Object>> result = new ArrayList<>();

        for (ExamAttempt attempt : attempts) {
            List<ExamAnswer> openAnswers = examAnswerRepository
                    .findByAttemptIdAndQuestionType(attempt.getId(), QuestionType.OPEN);

            for (ExamAnswer answer : openAnswers) {
                Map<String, Object> item = new HashMap<>();
                item.put("answerId", answer.getId());
                item.put("studentId", attempt.getStudentId());
                item.put("questionText", answer.getQuestion().getQuestionText());
                item.put("correctAnswer", answer.getQuestion().getCorrectAnswer());
                item.put("studentAnswer", answer.getAnswerText());
                item.put("pointsAwarded", answer.getPointsAwarded());
                item.put("maxPoints", answer.getQuestion().getPoints());
                item.put("isGraded", answer.getIsGraded());
                item.put("modifiedByProfessor", answer.getModifiedByProfessor());
                item.put("originalAiScore", answer.getOriginalAiScore());
                item.put("modifiedAt", answer.getModifiedAt());
                result.add(item);
            }
        }
        return result;
    }
    @Override
    public void updateAnswerScore(UUID answerId, Double pointsAwarded, UUID professorId) {
        examAnswerRepository.findById(answerId).ifPresent(answer -> {

            // Sauvegarder le score IA original si première modification
            if (answer.getOriginalAiScore() == null) {
                answer.setOriginalAiScore(answer.getPointsAwarded());
            }

            answer.setPointsAwarded(pointsAwarded);
            answer.setIsGraded(true);
            answer.setModifiedByProfessor(true);
            answer.setModifiedByProfessorId(professorId);
            answer.setModifiedAt(LocalDateTime.now());
            examAnswerRepository.save(answer);

            // Recalculer le score total
            ExamAttempt attempt = answer.getAttempt();
            double totalScore = examAnswerRepository
                    .findByAttemptId(attempt.getId())
                    .stream()
                    .mapToDouble(a -> a.getPointsAwarded() != null ? a.getPointsAwarded() : 0.0)
                    .sum();
            attempt.setScore(totalScore);
            examAttemptRepository.save(attempt);

            log.info("[Score] Modifié par prof={}: answer={} aiScore={} newScore={}",
                    professorId, answerId, answer.getOriginalAiScore(), pointsAwarded);
        });
    }
}