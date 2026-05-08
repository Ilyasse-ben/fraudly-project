# builde l'application
FROM maven:3.9.6-eclipse-temurin-21 AS builder
WORKDIR /app
COPY pom.xml .
COPY src ./src

RUN mvn clean package -DskipTests


# image de l'application
FROM openjdk:17.0.2-jdk
VOLUME /tmp
COPY --from=builder /app/target/*.jar  app.jar
EXPOSE 8080
ENTRYPOINT ["java","-jar", "app.jar"]
