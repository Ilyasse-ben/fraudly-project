package net.ilyasse.assessmentservice;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.jdbc.core.JdbcTemplate;

import java.time.LocalDateTime;
import java.util.UUID;

@SpringBootApplication
public class AssessmentServiceApplication {

    private static final String PROF_ID    = "11111111-1111-1111-1111-111111111111";
    private static final String EXAM1_ID   = "33333333-3333-3333-3333-333333333333";
    private static final String EXAM2_ID   = "44444444-4444-4444-4444-444444444444";
    private static final String COURSE1_ID = "66666666-6666-6666-6666-666666666666";
    private static final String COURSE2_ID = "77777777-7777-7777-7777-777777777777";

    public static void main(String[] args) {
        SpringApplication.run(AssessmentServiceApplication.class, args);
    }

    @Bean
    public CommandLineRunner seedExams(JdbcTemplate jdbcTemplate) {
        return args -> {
            Long count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM exams", Long.class);
            if (count != null && count == 0) {
                LocalDateTime now = LocalDateTime.now();

                jdbcTemplate.update(
                        "INSERT INTO exams (id, title, topic, duration_minutes, status, version, course_id, professor_id, created_at) VALUES (?::uuid, ?, ?, ?, ?, ?, ?::uuid, ?::uuid, ?)",
                        EXAM1_ID, "Machine Learning Midterm", "Supervised Learning", 60, "DRAFT", 1, COURSE1_ID, PROF_ID, now
                );

                jdbcTemplate.update(
                        "INSERT INTO exams (id, title, topic, duration_minutes, status, version, course_id, professor_id, created_at) VALUES (?::uuid, ?, ?, ?, ?, ?, ?::uuid, ?::uuid, ?)",
                        EXAM2_ID, "Cloud Computing Final", "AWS", 90, "PUBLISHED", 1, COURSE2_ID, PROF_ID, now
                );

                // Q1 — QCM_SINGLE
                String q1Id = UUID.randomUUID().toString();
                jdbcTemplate.update(
                        "INSERT INTO exam_questions (id, exam_id, order_index, type, question_text, correct_answer, points, edited_by_teacher, generated_by_ai) VALUES (?::uuid, ?::uuid, ?, ?, ?, ?, ?, ?, ?)",
                        q1Id, EXAM1_ID, 1, "QCM_SINGLE", "Which algorithm is used for classification?", "Logistic Regression", 1, false, false
                );

                String[] labels  = {"A", "B", "C", "D"};
                String[] texts   = {"Logistic Regression", "K-Means", "PCA", "Linear Regression"};
                boolean[] correct = {true, false, false, false};
                for (int i = 0; i < texts.length; i++) {
                    jdbcTemplate.update(
                            "INSERT INTO question_choices (id, question_id, label, text, is_correct) VALUES (?::uuid, ?::uuid, ?, ?, ?)",
                            UUID.randomUUID().toString(), q1Id, labels[i], texts[i], correct[i]
                    );
                }

                // Q2 — TRUE_FALSE
                jdbcTemplate.update(
                        "INSERT INTO exam_questions (id, exam_id, order_index, type, question_text, correct_answer, points, edited_by_teacher, generated_by_ai) VALUES (?::uuid, ?::uuid, ?, ?, ?, ?, ?, ?, ?)",
                        UUID.randomUUID().toString(), EXAM1_ID, 2, "TRUE_FALSE",
                        "Neural networks require labeled data for supervised learning", "TRUE", 2, false, false
                );

                // Q3 — OPEN
                jdbcTemplate.update(
                        "INSERT INTO exam_questions (id, exam_id, order_index, type, question_text, correct_answer, points, edited_by_teacher, generated_by_ai) VALUES (?::uuid, ?::uuid, ?, ?, ?, ?, ?, ?, ?)",
                        UUID.randomUUID().toString(), EXAM1_ID, 3, "OPEN",
                        "Explain the difference between overfitting and underfitting", null, 4, false, false
                );
            }
        };
    }
}
