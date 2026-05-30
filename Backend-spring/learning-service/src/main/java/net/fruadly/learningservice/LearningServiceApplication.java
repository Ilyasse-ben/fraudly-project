package net.fruadly.learningservice;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Bean;
import org.springframework.jdbc.core.JdbcTemplate;

import java.sql.Date;
import java.time.LocalDate;
import java.util.UUID;

@SpringBootApplication
@EnableFeignClients
public class LearningServiceApplication {

    private static final String STUDENT_ID = "22222222-2222-2222-2222-222222222222";
    private static final String COURSE1_ID = "66666666-6666-6666-6666-666666666666";
    private static final String COURSE2_ID = "77777777-7777-7777-7777-777777777777";

    public static void main(String[] args) {
        SpringApplication.run(LearningServiceApplication.class, args);
    }

    @Bean
    public CommandLineRunner seedCourses(JdbcTemplate jdbcTemplate) {
        return args -> {
            Long count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM courses", Long.class);
            if (count != null && count == 0) {
                Date today = Date.valueOf(LocalDate.now());

                jdbcTemplate.update(
                        "INSERT INTO courses (id, title, description, cours_code, course_date) VALUES (?::uuid, ?, ?, ?, ?)",
                        COURSE1_ID, "Machine Learning", "Introduction to ML algorithms", "ML101", today
                );

                jdbcTemplate.update(
                        "INSERT INTO courses (id, title, description, cours_code, course_date) VALUES (?::uuid, ?, ?, ?, ?)",
                        COURSE2_ID, "Cloud Computing", "AWS and cloud infrastructure", "CC202", today
                );

                jdbcTemplate.update(
                        "INSERT INTO chapters (id, title, index, date_chapitre, course_id) VALUES (?::uuid, ?, ?, ?, ?::uuid)",
                        UUID.randomUUID().toString(), "Introduction to Supervised Learning", 1L, today, COURSE1_ID
                );

                jdbcTemplate.update(
                        "INSERT INTO chapters (id, title, index, date_chapitre, course_id) VALUES (?::uuid, ?, ?, ?, ?::uuid)",
                        UUID.randomUUID().toString(), "Neural Networks Fundamentals", 2L, today, COURSE1_ID
                );

                jdbcTemplate.update(
                        "INSERT INTO enrollments (id, student_id, course_id, enrollment_date) VALUES (?::uuid, ?::uuid, ?::uuid, ?)",
                        UUID.randomUUID().toString(), STUDENT_ID, COURSE1_ID, today
                );
            }
        };
    }
}
