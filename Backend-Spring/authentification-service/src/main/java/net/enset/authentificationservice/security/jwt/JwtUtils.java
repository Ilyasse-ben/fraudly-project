package net.enset.authentificationservice.security.jwt;


import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.util.Date;
import java.util.Base64;
import java.util.UUID;

/**
 * @author ELHAID Yousef
 **/

@Component
public class JwtUtils {

    private static final String USER_ID_CLAIM = "userId";

    @Value("${jwt.secret}")
    private String jwtSecret;

    @Value("${jwt.expiration}")
    private long jwtExpiration;

    @Value("${jwt.refresh-expiration}")
    private long refreshExpiration;

    private SecretKey getSigningKey() {
        byte[] keyBytes = Base64.getDecoder().decode(jwtSecret);
        return Keys.hmacShaKeyFor(keyBytes);
    }

    public String generateAccessToken(UUID userId, String role) {
        return Jwts.builder()
                .subject(userId.toString())
                .claim(USER_ID_CLAIM, userId.toString())
                .claim("role", role)
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + jwtExpiration))
                .signWith(getSigningKey())
                .compact();
    }

    public String generateRefreshToken(UUID userId) {
        return Jwts.builder()
                .subject(userId.toString())
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + refreshExpiration))
                .signWith(getSigningKey())
                .compact();
    }

    public UUID extractUserId(String token) {
        Claims claims = parseClaims(token);

        String userIdValue = claims.get(USER_ID_CLAIM, String.class);
        if (userIdValue == null || userIdValue.isBlank()) {
            userIdValue = claims.getSubject();
        }

        return parseUserId(userIdValue);
    }

    public String extractRole(String token) {
        return parseClaims(token).get("role", String.class);
    }

    public boolean isTokenValid(String token) {
        try {
            Claims claims = parseClaims(token);
            validateUserIdClaims(claims);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }

    private Claims parseClaims(String token) {
        if (token == null || token.isBlank()) {
            throw new IllegalArgumentException("Token cannot be blank");
        }

        return Jwts.parser()
                .verifyWith(getSigningKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    private UUID parseUserId(String userId) {
        if (userId == null || userId.isBlank()) {
            throw new JwtException("Missing user id claim");
        }

        try {
            return UUID.fromString(userId);
        } catch (IllegalArgumentException ex) {
            throw new JwtException("Invalid user id claim", ex);
        }
    }

    private void validateUserIdClaims(Claims claims) {
        String userIdClaim = claims.get(USER_ID_CLAIM, String.class);
        String subject = claims.getSubject();

        if (userIdClaim != null && !userIdClaim.isBlank()) {
            UUID claimUserId = parseUserId(userIdClaim);
            UUID subjectUserId = parseUserId(subject);

            if (!claimUserId.equals(subjectUserId)) {
                throw new JwtException("Token subject and userId claim do not match");
            }

            return;
        }

        parseUserId(subject);
    }
}
