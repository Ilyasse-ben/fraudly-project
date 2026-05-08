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


    public static void main(String[] args) {
        SpringApplication.run(LearningServiceApplication.class, args);
    }


    @Bean
    public CommandLineRunner commandLineRunner(ChapterRepository chapterRepository, CoursRepository coursRepository) {

        return args -> {
            Chapter chapter=chapterRepository.save(new Chapter());
            Cours cours=new Cours();
            chapter.setCours(coursRepository.save(cours));
            chapterRepository.save(chapter);

        };

    }



}
