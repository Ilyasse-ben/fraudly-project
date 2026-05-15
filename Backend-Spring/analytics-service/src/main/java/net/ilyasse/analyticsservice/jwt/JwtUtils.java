package net.ilyasse.analyticsservice.jwt;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.UUID;

@Component
public class JwtUtils {

    private static final String USER_ID_CLAIM = "userId";
    private static final String ROLE_CLAIM = "role";

    @Value("${jwt.secret}")
    private String jwtSecret;

    private SecretKey getSigningKey() {
        byte[] keyBytes;
        try {
            keyBytes = Base64.getDecoder().decode(jwtSecret);
        } catch (IllegalArgumentException e) {
            keyBytes = jwtSecret.getBytes(StandardCharsets.UTF_8);
        }
        return Keys.hmacShaKeyFor(keyBytes);
    }

    public UUID extractUserId(String token) {
        Claims claims = parseClaims(token);
        String userIdValue = claims.get(USER_ID_CLAIM, String.class);
        if (userIdValue == null) userIdValue = claims.getSubject();
        return UUID.fromString(userIdValue);
    }

    public String extractRole(String token) {
        String role = parseClaims(token).get(ROLE_CLAIM, String.class);
        if (role == null || role.isBlank()) throw new JwtException("Missing role");
        return role;
    }

    public boolean isTokenValid(String token) {
        try {
            parseClaims(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }

    private Claims parseClaims(String token) {
        return Jwts.parser()
                .verifyWith(getSigningKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
}