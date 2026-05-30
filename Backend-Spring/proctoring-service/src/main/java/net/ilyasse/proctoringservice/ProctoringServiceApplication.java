package net.ilyasse.proctoringservice;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.context.annotation.Bean;
import org.springframework.jdbc.core.JdbcTemplate;

import java.time.LocalDateTime;
import java.util.UUID;

@SpringBootApplication
@EnableDiscoveryClient
public class ProctoringServiceApplication {

    private static final String STUDENT_ID = "22222222-2222-2222-2222-222222222222";
    private static final String EXAM1_ID   = "33333333-3333-3333-3333-333333333333";
    private static final String SESSION_ID = "55555555-5555-5555-5555-555555555555";

    public static void main(String[] args) {
        SpringApplication.run(ProctoringServiceApplication.class, args);
    }

    @Bean
    public CommandLineRunner seedProctoringData(JdbcTemplate jdbcTemplate) {
        return args -> {
            Long count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM proctoring_sessions", Long.class);
            if (count != null && count == 0) {
                LocalDateTime now = LocalDateTime.now();

                jdbcTemplate.update(
                        "INSERT INTO proctoring_sessions (id, student_id, exam_id, attempt_id, status, fraud_score, started_at) VALUES (?::uuid, ?::uuid, ?::uuid, ?::uuid, ?, ?, ?)",
                        SESSION_ID, STUDENT_ID, EXAM1_ID, EXAM1_ID, "FLAGGED", 85, now
                );

                jdbcTemplate.update(
                        "INSERT INTO fraud_events (id, session_id, student_id, exam_id, event_type, confidence_score, detected_at) VALUES (?::uuid, ?::uuid, ?::uuid, ?::uuid, ?, ?, ?)",
                        UUID.randomUUID().toString(), SESSION_ID, STUDENT_ID, EXAM1_ID, "TAB_SWITCH", 0.9, now
                );

                jdbcTemplate.update(
                        "INSERT INTO fraud_events (id, session_id, student_id, exam_id, event_type, confidence_score, detected_at) VALUES (?::uuid, ?::uuid, ?::uuid, ?::uuid, ?, ?, ?)",
                        UUID.randomUUID().toString(), SESSION_ID, STUDENT_ID, EXAM1_ID, "DEVICE_MISMATCH", 0.8, now
                );
            }
        };
    }
}
