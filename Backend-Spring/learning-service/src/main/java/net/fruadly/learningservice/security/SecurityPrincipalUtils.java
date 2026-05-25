package net.fruadly.learningservice.security;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;

import java.util.UUID;

@Component
public class SecurityPrincipalUtils {

    public UUID requireUserId() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || authentication.getPrincipal() == null) {
            throw new IllegalStateException("No authenticated principal available");
        }

        Object principal = authentication.getPrincipal();
        String userIdString;

        if (principal instanceof String) {
            userIdString = (String) principal;
        } else {
            // Fallback if it somehow still comes in as something else
            userIdString = principal.toString();
        }

        try {
            return UUID.fromString(userIdString);
        } catch (IllegalArgumentException ex) {
            throw new IllegalStateException("Principal is not a valid UUID: " + userIdString, ex);
        }
    }
}
