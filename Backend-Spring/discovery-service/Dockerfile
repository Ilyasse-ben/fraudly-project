# Stage 1: Build
FROM maven:3.9.6-eclipse-temurin-17 AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn clean package -DskipTests

# Stage 2: Run
FROM eclipse-temurin:17-jre-alpine
RUN addgroup -S spring && adduser -S spring -G spring
USER spring:spring
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar

# Explicitly expose only 8761 for the discovery-service
EXPOSE 8761

# Using an array for the entrypoint ensures signal handling (SIGTERM)
# works correctly for graceful shutdowns
ENTRYPOINT ["java", "-jar", "app.jar"]