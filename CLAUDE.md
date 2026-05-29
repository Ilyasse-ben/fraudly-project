# 🤖 Claude System Directives: Fraudly Project

## 🎯 Project Overview
**Fraudly** is an AI-enhanced e-learning, assessment, and proctoring platform built using a distributed microservices architecture. It integrates traditional course management with advanced AI capabilities (RAG, intelligent tutoring, automated grading, and real-time behavioral proctoring).

**Primary Goal of the Assistant:** Maintain architectural integrity. Ensure secure service-to-service communication via Kafka or Feign Clients, enforce JWT-based authorization, and respect the strict boundaries between the Frontend, the Spring Boot ecosystem, and the Python AI services.

---

## 🏗️ Architecture & Tech Stack

### 1. Frontend (Web Application)
* **Framework:** Angular (TypeScript)
* **Architecture:** Standalone components, service-based HTTP communication.
* **Routing Strategy:** ALL external API calls MUST route through the API Gateway (`http://localhost:8080/api`). Never bypass the gateway to call microservices directly.
* **Auth:** Interceptor-driven JWT bearer token injection.

### 2. Backend - Core Services (Spring Boot / Java)
* **Framework:** Spring Boot 3.x, Spring Cloud, Java 17+
* **Databases:** PostgreSQL (Multiple schemas: `fraudly_auth`, `fraudly_learning`, etc.), Redis (Caching & live session states).
* **Communication:**
    * Synchronous: Spring Cloud OpenFeign & Spring Cloud Gateway.
    * Asynchronous: Apache Kafka.
* **Security:** Spring Security with stateless JWT filtering on every service.

### 3. Backend - AI Services (FastAPI / Python)
* **Framework:** FastAPI, Python 3.10+
* **Capabilities:** Retrieval-Augmented Generation (RAG), Multi-Agent workflows (Tutor Agent, Path Agent, Assessment Agent).
* **Data Stores:** ChromaDB (Vector DB for RAG).
* **Integration:** Consumes/Produces Kafka events and exposes REST endpoints for complex AI calculations.

---

## 🗺️ Microservices Map

| Service Name | Port | Description & Responsibilities |
| :--- | :--- | :--- |
| `discovery-service` | `8761` | Eureka Server for service registry and discovery. |
| `gateway-service` | `8080` | Spring Cloud Gateway. The single entry point for the frontend. Handles initial CORS and routing. |
| `authentification-service` | `8081` | Identity Provider. Handles `/login`, `/register`, JWT generation, and User entity management. |
| `assessment-service` | `8082` | Exam lifecycles, answer submissions, test configurations. Interfaces with AI backend for grading. |
| `learning-service` | `8083` | Catalogs, Courses, Chapters, and resource ingestion (S3 integration). |
| `analytics-service` | `8084` | Event-driven service. Consumes Kafka topics to build student learning profiles and topic frequencies. |
| `proctoring-service` | `8085` | Real-time session monitoring. Tracks `fraudScores` via Redis and manages `CollusionAlerts`. |
| `backend-ia` | `8000` | Python/FastAPI. Houses ChromaDB, document chunking, LLM routers, and specialized AI agents. |

---

## 🔄 Integration Rules & Patterns

### Security & JWT Protocol
1. The Frontend extracts the JWT from `auth-service` and stores it.
2. The Frontend `AuthInterceptor` attaches `Authorization: Bearer <token>` to all requests going to `:8080`.
3. Microservices DO NOT contact the auth service to validate tokens. They use `JwtFilter.java` and `JwtUtils.java` (using a shared `JWT_SECRET`) to decode and validate the token locally.
4. Always use `@PreAuthorize("hasRole('ROLE_NAME')")` at the controller level in Spring.

### Internal Communication
* **Synchronous (HTTP):** Use `@FeignClient` for fast, required data fetches (e.g., getting user details). Use `ServiceTokenProvider.java` to inject internal authentication headers for machine-to-machine requests.
* **Asynchronous (Event-Driven):** Use Kafka.
    * Examples: `proctor.collusion_suspected`, `tutor.interaction_logged`, `exam.scored`, `proctor.events`, `proctor.flagged`.
    * Define Producers and Consumers in their respective `kafka/` packages.

### Backend-IA Integration
* The Java services send requests to the Python service via HTTP (FastAPI endpoints) or via Kafka (for heavy processing like document ingestion).
* The Python service MUST return responses matching the Java DTOs (`assessment_schema.py` must align with `BackendAiGenerationRequest.java`).

---

## 💻 Development Conventions

### Angular Conventions
* Use `ng generate` for scaffolding.
* Keep components logic-light. Delegate HTTP calls and state management to `Injectable` services.
* Map backend responses accurately using TypeScript `interfaces` inside the `models/` directory to avoid `undefined` errors.

### Spring Boot Conventions
* **Layered Architecture:** Controller ➡️ Service ➡️ Repository. No business logic in Controllers.
* **DTO Pattern:** Never expose `@Entity` classes directly via REST. Always map entities to `Response/Request DTOs`.
* **Lombok:** Use `@Data`, `@Builder`, `@RequiredArgsConstructor` extensively to reduce boilerplate.
* **Transactions:** Annotate state-modifying service methods with `@Transactional`.
* **Packages:** `net.ilyasse.*` (assessment, proctoring, analytics, learning) / `net.enset.*` (auth)

### Python / FastAPI Conventions
* Enforce type hinting using Pydantic schemas (in `app/schemas/`).
* Separate AI logic into `agents/` and core orchestration into `services/`.
* Keep endpoints (`app/api/`) asynchronous (`async def`) wherever possible to handle high-latency LLM calls efficiently.

---

## 🐳 Infrastructure & Docker Topology
All services run on a shared custom bridge network: `fraudly-network`.

**Core Infrastructure Containers:**
* `pgdb` (PostgreSQL 15): Stores all relational data. Reachable at `pgdb:5432`.
* `kafka` (Confluent 7.6.0): KRaft mode. Reachable internally at `kafka:9092`.
* `redis` (Redis 7 Alpine): Live proctoring state + caching. Reachable at `redis:6379`.
* `chroma`: ChromaDB for vector embeddings. Required by `backend-ia`.

**Service Dependencies:**
`pgdb`, `kafka`, and `discovery-service` must pass health checks before any business microservice boots.

---

## 🛠️ Common Commands

### Docker
```bash
# Start everything
docker compose up -d

# Rebuild a specific service after code change
docker compose up --build <service_name>

# View logs
docker compose logs -f <service_name>

# Check running containers
docker compose ps
```

### Local Development (infrastructure via Docker, services local)
```bash
# Start infra only
docker compose up pgdb kafka redis -d

# Run services locally
cd Backend-Spring/authentification-service && mvn spring-boot:run   # :8081
cd Backend-Spring/assessment-service && mvn spring-boot:run          # :8082
cd Backend-Spring/proctoring-service && mvn spring-boot:run          # :8085

# Frontend
cd Frontend && npm start
```

### Swagger UIs (local)
* Auth: http://localhost:8081/swagger-ui.html
* Assessment: http://localhost:8082/swagger-ui.html
* Proctoring: http://localhost:8085/swagger-ui.html

---

## 🔑 Key Env Variables (.env)
```
JWT_SECRET=ZnJhdWRseS1zZWNyZXQta2V5LWZvci1qd3QtdG9rZW4tMjAyNQ==
JWT_EXPIRATION=900000
JWT_REFRESH_EXPIRATION=604800000
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
EUREKA_ZONE=http://discovery-service:8761/eureka/
DB_URL_AUTH=jdbc:postgresql://pgdb:5432/fraudly_auth
DB_URL_ASSESSMENT=jdbc:postgresql://pgdb:5432/fraudly_assessment
DB_URL_PROCTORING=jdbc:postgresql://pgdb:5432/fraudly_proctoring
REDIS_HOST=redis
REDIS_PORT=6379
AI_SERVICE_URL=http://backend-ia:8000
```

---

## 📋 Current Implementation Status
| Component | Status |
| :--- | :--- |
| authentification-service | ✅ Complete & Tested |
| assessment-service | ✅ Complete |
| proctoring-service | ✅ Entities + Redis + Kafka complete |
| analytics-service | ✅ Running |
| learning-service | ✅ Running |
| gateway-service | ✅ Running |
| backend-ia | ⚠️ ChromaDB dependency needed |
| Frontend ↔ Backend integration | 🔄 In Progress |
| CI/CD Pipeline | ⏳ Pending |

---

## 🚫 Hard Rules for Claude Code
1. **Never bypass the gateway.** Frontend always calls `:8080`.
2. **Never expose entities directly.** Always use DTOs.
3. **Never hardcode secrets.** Use `.env` / environment variables.
4. **Never add business logic to controllers.** It belongs in the service layer.
5. **Always add `@Transactional`** to write operations in services.
6. **Token validation is local** — microservices never call auth-service to validate JWTs.