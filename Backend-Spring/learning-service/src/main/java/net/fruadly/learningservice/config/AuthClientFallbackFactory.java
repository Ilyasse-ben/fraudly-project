package net.fruadly.learningservice.config;

import feign.FeignException;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ResponseStatusException;

@Component
public class AuthClientFallbackFactory implements FallbackFactory<AuthClient> {

    @Override
    public AuthClient create(Throwable cause) {
        return userId -> {
            if (cause instanceof FeignException feignException) {
                int status = feignException.status();
                if (status == 404) {
                    throw new ResponseStatusException(HttpStatus.NOT_FOUND, "User not found in auth service", cause);
                }
                if (status == 401 || status == 403) {
                    throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Unauthorized call to auth service", cause);
                }
            }
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Auth service unavailable", cause);
        };
    }
}