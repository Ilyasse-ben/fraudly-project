package net.ilyasse.analyticsservice;

import net.ilyasse.analyticsservice.entity.StudentLearningProfile;
import net.ilyasse.analyticsservice.entity.TopicFrequency;
import net.ilyasse.analyticsservice.repository.StudentLearningProfileRepository;
import net.ilyasse.analyticsservice.repository.TopicFrequencyRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.UUID;

@RestController
@SpringBootApplication
public class AnalyticsServiceApplication {

    private static final UUID STUDENT_ID = UUID.fromString("22222222-2222-2222-2222-222222222222");
    private static final UUID COURSE1_ID = UUID.fromString("66666666-6666-6666-6666-666666666666");

    public static void main(String[] args) {
        SpringApplication.run(AnalyticsServiceApplication.class, args);
    }

    @GetMapping("/index")
    public String ok() {
        return "hello";
    }

    @Bean
    public CommandLineRunner seedAnalytics(
            StudentLearningProfileRepository profileRepository,
            TopicFrequencyRepository topicFrequencyRepository) {
        return args -> {
            if (profileRepository.count() == 0) {
                StudentLearningProfile profile1 = StudentLearningProfile.builder()
                        .studentId(STUDENT_ID)
                        .courseId(COURSE1_ID)
                        .completedChaptersJson("[]")
                        .scoresJson("{\"cc1\":15,\"cc2\":14,\"exam\":16,\"average\":15.2,\"status\":\"Excellent\",\"studentName\":\"Yousef ELHAID\"}")
                        .weakTopicsJson("[\"Overfitting\",\"Regularization\"]")
                        .interactionsCount(24)
                        .lastInteractionAt(LocalDateTime.now())
                        .build();
                profileRepository.save(profile1);

                StudentLearningProfile profile2 = StudentLearningProfile.builder()
                        .studentId(UUID.randomUUID())
                        .courseId(COURSE1_ID)
                        .completedChaptersJson("[]")
                        .scoresJson("{\"cc1\":10,\"cc2\":9,\"exam\":11,\"average\":10.1,\"status\":\"Needs Review\",\"studentName\":\"Sara Amrani\"}")
                        .weakTopicsJson("[]")
                        .interactionsCount(5)
                        .lastInteractionAt(LocalDateTime.now())
                        .build();
                profileRepository.save(profile2);
            }

            if (topicFrequencyRepository.count() == 0) {
                TopicFrequency overfitting = new TopicFrequency();
                overfitting.setStudentId(STUDENT_ID);
                overfitting.setCourseId(COURSE1_ID);
                overfitting.setTopic("Overfitting");
                overfitting.setCount(14);
                overfitting.setLastAskedAt(LocalDateTime.now());
                topicFrequencyRepository.save(overfitting);

                TopicFrequency regularization = new TopicFrequency();
                regularization.setStudentId(STUDENT_ID);
                regularization.setCourseId(COURSE1_ID);
                regularization.setTopic("Regularization");
                regularization.setCount(10);
                regularization.setLastAskedAt(LocalDateTime.now());
                topicFrequencyRepository.save(regularization);
            }
        };
    }
}
