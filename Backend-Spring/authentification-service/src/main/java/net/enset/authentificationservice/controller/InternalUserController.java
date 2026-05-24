package net.enset.authentificationservice.controller;

import lombok.RequiredArgsConstructor;
import net.enset.authentificationservice.dto.response.UserDto;
import net.enset.authentificationservice.repository.UserRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.UUID;

import static org.springframework.http.HttpStatus.NOT_FOUND;

@RestController
@RequestMapping("/internal/users")
@RequiredArgsConstructor
public class InternalUserController {

    private final UserRepository userRepository;

    @GetMapping("/{id}")
    @PreAuthorize("hasAuthority('ROLE_INTERNAL')")
    public ResponseEntity<UserDto> getUserById(@PathVariable UUID id) {
        return ResponseEntity.ok(userRepository.findById(id)
                .map(user -> new UserDto(user.getId(), user.getEmail(), user.getRole().name()))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "User not found")));
    }
}