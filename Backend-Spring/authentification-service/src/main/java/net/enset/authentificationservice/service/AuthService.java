package net.enset.authentificationservice.service;


import lombok.RequiredArgsConstructor;
import net.enset.authentificationservice.dto.request.LoginRequest;
import net.enset.authentificationservice.dto.request.RegisterRequest;
import net.enset.authentificationservice.dto.response.AuthResponse;
import net.enset.authentificationservice.entity.Role;
import net.enset.authentificationservice.entity.User;
import net.enset.authentificationservice.repository.UserRepository;
import net.enset.authentificationservice.security.jwt.JwtUtils;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.util.UUID;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.UNAUTHORIZED;
import static org.springframework.http.HttpStatus.CONFLICT;

/**
 * @author ELHAID Yousef
 **/

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtils jwtUtils;
    private final AuthenticationManager authenticationManager;

    public AuthResponse register(RegisterRequest request) {
        if (userRepository.existsByEmail(request.getEmail())) {
                        throw new ResponseStatusException(CONFLICT, "Email already in use");
        }

        User user = User.builder()
                .fullName(request.getFullName())
                .email(request.getEmail())
                .password(passwordEncoder.encode(request.getPassword()))
                .role(request.getRole() != null ? request.getRole() : Role.ROLE_STUDENT)
                .enabled(true)
                .consentGivenAt(LocalDateTime.now())
                .build();

        User savedUser = userRepository.save(user);

        String accessToken = jwtUtils.generateAccessToken(savedUser.getId(), savedUser.getRole().name());
        String refreshToken = jwtUtils.generateRefreshToken(savedUser.getId());

        AuthResponse response = new AuthResponse();
        response.setAccessToken(accessToken);
        response.setRefreshToken(refreshToken);
        response.setUserId(savedUser.getId());
        response.setEmail(savedUser.getEmail());
        response.setRole(savedUser.getRole().name());
        return response;
    }

    public AuthResponse login(LoginRequest request) {
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        request.getEmail(),
                        request.getPassword()
                )
        );

        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new ResponseStatusException(UNAUTHORIZED, "Invalid credentials"));

        String accessToken = jwtUtils.generateAccessToken(user.getId(), user.getRole().name());
        String refreshToken = jwtUtils.generateRefreshToken(user.getId());

        AuthResponse resp = new AuthResponse();
        resp.setAccessToken(accessToken);
        resp.setRefreshToken(refreshToken);
        resp.setUserId(user.getId());
        resp.setEmail(user.getEmail());
        resp.setRole(user.getRole().name());
        return resp;
    }

    public AuthResponse refresh(String refreshToken) {
        if (!jwtUtils.isTokenValid(refreshToken)) {
                        throw new ResponseStatusException(BAD_REQUEST, "Invalid refresh token");
        }

        UUID userId = jwtUtils.extractUserId(refreshToken);

        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(UNAUTHORIZED, "Invalid refresh token"));

        String newAccessToken = jwtUtils.generateAccessToken(user.getId(), user.getRole().name());
        String newRefreshToken = jwtUtils.generateRefreshToken(user.getId());

        AuthResponse r = new AuthResponse();
        r.setAccessToken(newAccessToken);
        r.setRefreshToken(newRefreshToken);
        r.setUserId(user.getId());
        r.setEmail(user.getEmail());
        r.setRole(user.getRole().name());
        return r;
    }
}