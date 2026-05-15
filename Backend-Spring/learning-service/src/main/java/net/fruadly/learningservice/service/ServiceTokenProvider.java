package net.fruadly.learningservice.service;

import net.fruadly.learningservice.security.jwt.JwtUtils;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
public class ServiceTokenProvider {

    private final JwtUtils jwtUtils;

    private static final String SERVICE_ID = "learning-service";

    public ServiceTokenProvider(JwtUtils jwtUtils) {
        this.jwtUtils = jwtUtils;
    }

    public String generateToken() {
        return jwtUtils.generateAccessToken(
                UUID.fromString("00000000-0000-0000-0000-000000000001"),
                "ROLE_INTERNAL"
        );
    }
}