package net.ilyasse.assessmentservice.service;

import net.ilyasse.assessmentservice.jwt.JwtUtils;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
public class ServiceTokenProvider {

    private final JwtUtils jwtUtils;

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