package net.fruadly.learningservice.config;

import feign.RequestInterceptor;
import net.fruadly.learningservice.service.ServiceTokenProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class FeignConfig {

    private final ServiceTokenProvider tokenProvider;

    public FeignConfig(ServiceTokenProvider tokenProvider) {
        this.tokenProvider = tokenProvider;
    }

    @Bean
    public RequestInterceptor serviceAuthInterceptor() {
        return requestTemplate -> {
            String token = tokenProvider.generateToken();
            requestTemplate.header("Authorization", "Bearer " + token);
        };
    }
}