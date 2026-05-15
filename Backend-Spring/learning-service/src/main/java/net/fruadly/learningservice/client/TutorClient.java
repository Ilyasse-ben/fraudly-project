package net.fruadly.learningservice.client;


import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.fruadly.learningservice.dto.TutorAskRequest;
import net.fruadly.learningservice.dto.TutorAskResponse;
import net.fruadly.learningservice.service.ServiceTokenProvider;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

@Slf4j
@Component
@RequiredArgsConstructor
public class TutorClient {

        private final RestTemplate restTemplate;
        private final ServiceTokenProvider tokenProvider;

        @Value("${ai.service.url}")
        private String aiServiceUrl;

        public TutorAskResponse askTutor(TutorAskRequest request) {

                HttpHeaders headers = new HttpHeaders();

                headers.setContentType(MediaType.APPLICATION_JSON);

                String token = tokenProvider.generateToken();
                log.info("Generated internal token: {}", token);
                headers.set("Authorization", "Bearer " + token);

                HttpEntity<TutorAskRequest> entity = new HttpEntity<>(request, headers);

                ResponseEntity<TutorAskResponse> response = restTemplate.exchange(
                                aiServiceUrl + "/tutor/ask",
                                HttpMethod.POST,
                                entity,
                                TutorAskResponse.class
                );

                return response.getBody();
        }
}