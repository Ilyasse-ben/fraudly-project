package net.fruadly.learningservice;

import net.fruadly.learningservice.entity.Chapter;
import net.fruadly.learningservice.entity.Cours;
import net.fruadly.learningservice.repository.ChapterRepository;
import net.fruadly.learningservice.repository.CoursRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

import java.security.SecureRandom;

@SpringBootApplication
public class LearningServiceApplication {
    public static String generate(int length) {
         final String CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
         final SecureRandom RANDOM = new SecureRandom();
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
            System.out.println("££££££££££££££££££££££££££££££££££££££");
            System.out.println(""+coursRepository.findByCoursCode(token).getId());
            System.out.println("££££££££££££££££££££££££££££££££££££££");

        };

    }



}
