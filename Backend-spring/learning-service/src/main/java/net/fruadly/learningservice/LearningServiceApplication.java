package net.fruadly.learningservice;

import net.fruadly.learningservice.entity.Chapter;
import net.fruadly.learningservice.entity.Cours;
import net.fruadly.learningservice.repository.ChapterRepository;
import net.fruadly.learningservice.repository.CoursRepository;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.security.SecureRandom;

@SpringBootApplication
@EnableFeignClients
public class LearningServiceApplication {
    private static final Logger log = LoggerFactory.getLogger(LearningServiceApplication.class);
    private static final SecureRandom RANDOM = new SecureRandom();

    public static String generate(int length) {
         final String CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        StringBuilder sb = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
            int index = RANDOM.nextInt(CHARACTERS.length());
            sb.append(CHARACTERS.charAt(index));
        }

        return sb.toString();
    }

    public static void main(String[] args) {
        SpringApplication.run(LearningServiceApplication.class, args);
    }


    @Bean
    public CommandLineRunner commandLineRunner(ChapterRepository chapterRepository, CoursRepository coursRepository) {

        return args -> {
            Chapter chapter=chapterRepository.save(new Chapter());
            Cours cours=new Cours();
            String token=generate(8);
            cours.setCoursCode(token);
            chapter.setCours(coursRepository.save(cours));
            chapterRepository.save(chapter);
            log.info("Seeded sample course id: {}", coursRepository.findByCoursCode(token).getId());

        };

    }



}
