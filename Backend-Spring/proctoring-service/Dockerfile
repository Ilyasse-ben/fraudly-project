# Stage 1: Build
FROM maven:3.9.6-eclipse-temurin-17 AS builder
WORKDIR /app
# Cache dependencies
COPY pom.xml .
RUN mvn dependency:go-offline -B
# Copy source
COPY src ./src
RUN mvn clean package -DskipTests

# Stage 2: Run
FROM eclipse-temurin:17-jre-alpine
# Create a non-root user
RUN addgroup -S spring && adduser -S spring -G spring
USER spring:spring
WORKDIR /app
# Copy the built jar from the builder stage
COPY --from=builder /app/target/*.jar app.jar
# Expose the correct port (adjust per service)
EXPOSE 8081
ENTRYPOINT ["java", "-jar", "app.jar"]