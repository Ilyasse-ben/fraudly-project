package net.enset.authentificationservice;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

import java.time.LocalDateTime;

@SpringBootApplication
public class AuthentificationServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(AuthentificationServiceApplication.class, args);
    }

    @Bean
    public CommandLineRunner seedUsers(JdbcTemplate jdbcTemplate) {
        return args -> {
            Long count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM users", Long.class);
            if (count != null && count == 0) {
                String encoded = new BCryptPasswordEncoder().encode("password123");
                LocalDateTime now = LocalDateTime.now();

                jdbcTemplate.update(
                        "INSERT INTO users (id, full_name, email, password, role, enabled, created_at) VALUES (?::uuid, ?, ?, ?, ?, ?, ?)",
                        "11111111-1111-1111-1111-111111111111",
                        "Prof. Ahmed Benali",
                        "prof@fraudly.ma",
                        encoded,
                        "ROLE_TEACHER",
                        true,
                        now
                );

                jdbcTemplate.update(
                        "INSERT INTO users (id, full_name, email, password, role, enabled, created_at) VALUES (?::uuid, ?, ?, ?, ?, ?, ?)",
                        "22222222-2222-2222-2222-222222222222",
                        "Yousef ELHAID",
                        "student@fraudly.ma",
                        encoded,
                        "ROLE_STUDENT",
                        true,
                        now
                );
            }
        };
    }
}
