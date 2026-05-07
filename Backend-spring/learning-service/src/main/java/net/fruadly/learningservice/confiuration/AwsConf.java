package net.fruadly.learningservice.confiuration;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.AwsSessionCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.S3Configuration;

import java.net.URI;

@Configuration
public class AwsConf {
    @Value("${aws.accessKey}") 
    private String accessKey;

    @Value("${aws.secretKey}")
    private String secretKey;
    @Value("${aws.sessionToken}")
    private String sessionToken;

    @Value("${aws.region}")
    private String region;

    @Bean
    public S3Client s3Client() {
        return S3Client.builder()
                .region(Region.of(region))
                .credentialsProvider(
                        StaticCredentialsProvider.create(
                                AwsSessionCredentials.create(accessKey, secretKey, sessionToken)
                        )
                )
                // Optionnel : force l'accélération ou le style d'URL si nécessaire
                .serviceConfiguration(S3Configuration.builder()
                        .pathStyleAccessEnabled(true) // Essaie de passer à true si l'erreur persiste
                        .build())
                .build();
    }
}
