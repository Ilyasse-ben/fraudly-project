package net.ilyasse.assessmentservice.dto.request;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import net.ilyasse.assessmentservice.enums.Difficulty;
import net.ilyasse.assessmentservice.enums.QuestionType;
import java.util.List;
/**
 * @author ELHAID Yousef
 **/

@Data
public class ExamConfigRequest {

    @NotNull
    private Long courseId;

    @NotNull
    private Long professorId;

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
    private List<Integer> chapterIds;

    @NotNull
    private Difficulty difficulty;
}
