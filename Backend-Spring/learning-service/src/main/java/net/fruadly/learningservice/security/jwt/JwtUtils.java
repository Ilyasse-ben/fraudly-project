package net.fruadly.learningservice.security.jwt;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.util.Base64;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.UUID;

/**
 * JWT Token generation and validation utility
 */
@Component
public class JwtUtils {

    private static final String USER_ID_CLAIM = "userId";
    private static final String ROLE_CLAIM = "role";

    @Value("${jwt.secret}")
    private String jwtSecret;

    @Value("${jwt.expiration}")
    private long jwtExpiration;

    @Value("${jwt.refresh-expiration}")
    private long refreshExpiration;

    private SecretKey getSigningKey() {
        byte[] keyBytes;
        try {
            keyBytes = Base64.getDecoder().decode(jwtSecret);
        } catch (IllegalArgumentException e) {
            keyBytes = jwtSecret.getBytes(StandardCharsets.UTF_8);
        }
        return Keys.hmacShaKeyFor(keyBytes);
    }

    /**
     * Generate an access token with userId and role claims
     */
    public String generateAccessToken(UUID userId, String role) {
        return Jwts.builder()
                .subject(userId.toString())
                .claim(USER_ID_CLAIM, userId.toString())
                .claim(ROLE_CLAIM, role)
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + jwtExpiration))
                .signWith(getSigningKey())
                .compact();
    }

    /**
     * Generate a refresh token with userId as subject
     */
    public String generateRefreshToken(UUID userId) {
        return Jwts.builder()
                .subject(userId.toString())
                .claim(USER_ID_CLAIM, userId.toString())
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + refreshExpiration))
                .signWith(getSigningKey())
                .compact();
    }

    /**
     * Extract userId (UUID) from token
     */
    public UUID extractUserId(String token) {
        Claims claims = parseClaims(token);
        validateUserIdClaims(claims);

        String userIdValue = claims.get(USER_ID_CLAIM, String.class);
        if (userIdValue == null || userIdValue.isBlank()) {
            userIdValue = claims.getSubject();
        }

        if (userIdValue == null || userIdValue.isBlank()) {
            throw new JwtException("Missing userId in token");
        }

        try {
            return UUID.fromString(userIdValue);
        } catch (IllegalArgumentException ex) {
            throw new JwtException("Invalid userId in token", ex);
        }
    }

    /**
     * Extract role claim from token
     */
    public String extractRole(String token) {
        String role = parseClaims(token).get(ROLE_CLAIM, String.class);
        if (role == null || role.isBlank()) {
            throw new JwtException("Missing role in token");
        }
        return role;
    }

    /**
     * Validate token integrity and expiration
     */
    public boolean isTokenValid(String token) {
        try {
            Claims claims = parseClaims(token);
            validateUserIdClaims(claims);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }

    /**
     * Parse and verify token claims
     */
    private Claims parseClaims(String token) {
        if (token == null || token.isBlank()) {
            throw new JwtException("Token is missing");
        }

        return Jwts.parser()
                .verifyWith(getSigningKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    private void validateUserIdClaims(Claims claims) {
        String userIdClaim = claims.get(USER_ID_CLAIM, String.class);
        String subject = claims.getSubject();

        if (subject == null || subject.isBlank()) {
            throw new JwtException("Missing subject in token");
        }

        UUID subjectUserId = parseUuid(subject);

        if (userIdClaim == null || userIdClaim.isBlank()) {
            return;
        }

        UUID claimUserId = parseUuid(userIdClaim);
        if (!claimUserId.equals(subjectUserId)) {
            throw new JwtException("Token subject and userId claim mismatch");
        }
    }

    private UUID parseUuid(String value) {
        if (value == null || value.isBlank()) {
            throw new JwtException("Missing UUID value in token");
        }

        try {
            return UUID.fromString(value);
        } catch (IllegalArgumentException ex) {
            throw new JwtException("Invalid UUID value in token", ex);
        }
    }
}
