package net.fruadly.learningservice.config;

import net.fruadly.learningservice.dto.UserDto;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import java.util.UUID;

@FeignClient(
        name = "authClient",
        url = "${services.auth.base-url}",
        configuration = AuthFeignConfig.class,
        fallbackFactory = AuthClientFallbackFactory.class
)
public interface AuthClient {

    @GetMapping("/internal/users/{id}")
    UserDto getUserById(@PathVariable("id") UUID userId);
}