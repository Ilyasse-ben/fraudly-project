package net.ilyasse.discaveryservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.netflix.eureka.server.EnableEurekaServer;

@SpringBootApplication
@EnableEurekaServer

public class DiscaveryServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(DiscaveryServiceApplication.class, args);
    }

}
