package net.fruadly.learningservice.controller;

import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.dto.TutorAskRequest;
import net.fruadly.learningservice.dto.TutorAskResponse;
import net.fruadly.learningservice.service.TutorService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/learning/tutor")
@RequiredArgsConstructor
public class TutorController {

    private final TutorService tutorService;

    @PostMapping("/ask")
    public TutorAskResponse ask(
            @RequestBody TutorAskRequest request
    ) {
        return tutorService.ask(request);
    }
}