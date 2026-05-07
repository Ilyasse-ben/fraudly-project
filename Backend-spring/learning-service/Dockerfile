# builde l'application
FROM maven:3.9.6-eclipse-temurin-21 AS builder
WORKDIR /app
COPY pom.xml /app/
COPY src /app/src

RUN mvn -f /app/pom.xml clean package -DskipTests


# image de l'application
FROM eclipse-temurin:21-jdk
VOLUME /tmp
COPY --from=builder /app/target/*.jar  /app/app.jar
EXPOSE 8084
ENTRYPOINT ["java","-jar", "/app/app.jar"]
