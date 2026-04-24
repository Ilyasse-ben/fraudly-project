package net.ilyasse.assessmentservice.dto.response;

import lombok.Builder;
import lombok.Data;
import net.ilyasse.assessmentservice.enums.Difficulty;
import net.ilyasse.assessmentservice.enums.QuestionType;
import java.util.List;

/**
 * @author ELHAID Yousef
 **/
@Data
@Builder
public class ExamQuestionResponse {
    private Long id;
    private Integer orderIndex;
    private QuestionType type;
    private String questionText;
    private String correctAnswer;
    private String explanation;
    private Integer points;
    private Difficulty difficulty;
    private Boolean generatedByAi;
    private Boolean editedByTeacher;
    private List<QuestionChoiceResponse> choices;
}
