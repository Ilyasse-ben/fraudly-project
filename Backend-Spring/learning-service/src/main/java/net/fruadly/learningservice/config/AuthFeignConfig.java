package net.fruadly.learningservice.config;

import feign.RequestInterceptor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;

public class AuthFeignConfig {

    @Bean
    public RequestInterceptor internalAuthRequestInterceptor(
            @Value("${services.auth.internal-secret}") String internalSecret) {
        return template -> template.header("X-Internal-Token", internalSecret);
    }
}