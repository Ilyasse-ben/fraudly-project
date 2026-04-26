package net.ilyasse.assessmentservice.dto.request;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import net.ilyasse.assessmentservice.enums.Difficulty;
import net.ilyasse.assessmentservice.enums.QuestionType;
import java.util.List;
import java.util.UUID;
/**
 * @author ELHAID Yousef
 **/

@Data
public class ExamConfigRequest {

    private String topic;

    @NotNull
    private UUID courseId;

    @NotNull
    private UUID professorId;

    @NotNull
    private String title;

    @NotNull
    private Integer durationMinutes;

    @NotNull
    @Min(0)
    private Integer nbQcm;

    @NotNull
    private QuestionType qcmType;

    @NotNull
    @Min(0)
    private Integer nbTrueFalse;

    @NotNull
    @Min(0)
    private Integer nbOpen;

    @NotNull
    private List<UUID> chapterIds;

    @NotNull
    private Difficulty difficulty;

    private Integer topK;

    private Boolean includeExplanations;

    private String professorInstructions;
}
