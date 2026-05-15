package net.fruadly.learningservice.service;

import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.client.TutorClient;
import net.fruadly.learningservice.dto.TutorAskRequest;
import net.fruadly.learningservice.dto.TutorAskResponse;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class TutorService {

    private final TutorClient tutorClient;

    public TutorAskResponse ask(TutorAskRequest request) {
        return tutorClient.askTutor(request);
    }
}