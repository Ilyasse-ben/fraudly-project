package net.ilyasse.assessmentservice.dto.response;


import lombok.Builder;
import lombok.Data;
import net.ilyasse.assessmentservice.enums.Difficulty;
import net.ilyasse.assessmentservice.enums.ExamStatus;
import java.time.LocalDateTime;
import java.util.List;
/**
 * @author ELHAID Yousef
 **/
@Data
@Builder
public class ExamResponse {
    private Long id;
    private String title;
    private String topic;
    private Difficulty difficulty;
    private ExamStatus status;
    private Integer version;
    private Long courseId;
    private Long professorId;
    private Integer durationMinutes;
    private LocalDateTime createdAt;
    private LocalDateTime publishedAt;
    private LocalDateTime startDate;
    private LocalDateTime endDate;
    private List<ExamQuestionResponse> questions;
}
