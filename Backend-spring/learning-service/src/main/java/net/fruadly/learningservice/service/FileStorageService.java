package net.fruadly.learningservice.service;

import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.UUID;

@Service
public class FileStorageService {

    // Chemin où les fichiers seront stockés (ex: "uploads/")
    private final Path root = Paths.get("uploads");

    public void init() {
        try {
            if (!Files.exists(root)) {
                Files.createDirectory(root);
            }
        } catch (IOException e) {
            throw new RuntimeException("Impossible d'initialiser le dossier de stockage");
        }
    }

    public String save(MultipartFile file) {
        try {
            // On génère un nom unique pour éviter les écrasements
            this.init();
            String fileName = UUID.randomUUID().toString() + "_" + file.getOriginalFilename();
            Files.copy(file.getInputStream(), this.root.resolve(fileName));
            return this.root.resolve(fileName).toString(); // Retourne le path stocké
        } catch (Exception e) {
            throw new RuntimeException("Erreur lors du stockage du fichier : " + e.getMessage());
        }
    }
}
