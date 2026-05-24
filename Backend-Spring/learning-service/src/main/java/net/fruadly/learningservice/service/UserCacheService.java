package net.fruadly.learningservice.service;

import lombok.RequiredArgsConstructor;
import net.fruadly.learningservice.config.AuthClient;
import net.fruadly.learningservice.dto.UserDto;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
@RequiredArgsConstructor
public class UserCacheService {

    private final AuthClient authClient;

    @Cacheable(value = "users", key = "#userId")
    public UserDto getUser(UUID userId) {
        return authClient.getUserById(userId);
    }

    @CacheEvict(value = "users", key = "#userId")
    public void evictUser(UUID userId) {
        // Intentionally empty: evicts cached user projections when user data changes.
    }
}