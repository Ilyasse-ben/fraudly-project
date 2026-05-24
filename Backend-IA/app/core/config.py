from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = ["*"]

    # ── OCR ───────────────────────────────────────────────
    OCR_LANG: str = "fra+eng"
    PDF_IMAGE_STRATEGY: str = "text_only"

    # ── Embedding ─────────────────────────────────────────
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_WARMUP_ON_STARTUP: bool = False

    # ── ChromaDB ──────────────────────────────────────────
    CHROMA_PATH: str = "./chroma_db_native_miniLM384"
    CHROMA_COLLECTION: str = "fraudly_knowledge_miniLM384"
    CHROMA_AUTO_RESET_ON_DIMENSION_MISMATCH: bool = True
    VECTOR_STORE_BACKEND: str = "chroma"
    CHROMA_HTTP_HOST: str = ""
    CHROMA_HTTP_PORT: int = 8001
    CHROMA_HTTP_SSL: bool = False

    # ── Chunking ──────────────────────────────────────────
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100

    # ── Retrieval ─────────────────────────────────────────
    DEFAULT_TOP_K: int = 5
    MAX_TOP_K: int = 20

    # ── LLM ───────────────────────────────────────────────
    # Provider principal recommandé (gratuit): Groq.
    # Fallback recommandé: Gemini Flash.
    LLM_PROVIDER: str = "groq"
    LLM_FALLBACK_PROVIDER: str = "gemini"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.1

    # ── Kafka ─────────────────────────────────────────────
    KAFKA_ENABLED: bool = True
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9094"
    KAFKA_GROUP_ID: str = "fraudly-ia-service"
    KAFKA_TOPIC_RESOURCE_UPLOADED: str = "resource_uploaded"
    KAFKA_TOPIC_EXAM_SUBMITTED: str = "exam_submitted"
    KAFKA_TOPIC_EXAM_CORRECTION_REQUESTED: str = "exam.correction.requested"
    KAFKA_TOPIC_EXAM_FREETEXT: str = "exam.freetext"
    KAFKA_TOPIC_EXAM_SCORED: str = "exam.scored"
    KAFKA_TOPIC_AI_RESULTS: str = "ai_results"
    KAFKA_TOPIC_FRAUD_ALERTS: str = "fraud_alerts"
    KAFKA_TOPIC_COLLUSION_SUSPECTED: str = "proctor.collusion_suspected"
    KAFKA_TOPIC_LEARNING_PATH_UPDATE: str = "learning_path_update"
    KAFKA_TOPIC_STUDENT_BLOCKED: str = "tutor.student_blocked"

    # ── Session Memory (Redis) ─────────────────────────
    SESSION_MEMORY_ENABLED: bool = True
    REDIS_URL: str = "redis://localhost:6379/0"
    SESSION_MEMORY_TTL_SECONDS: int = 86400
    SESSION_MEMORY_MAX_TURNS: int = 6

    # ── Tutor monitor (student blocked detection) ───────
    TUTOR_BLOCK_SIMILARITY_THRESHOLD: float = 0.78
    TUTOR_BLOCK_MIN_TURNS: int = 4
    TUTOR_BLOCK_LOOKBACK_WINDOW: int = 4
    TUTOR_BLOCK_HIGH_SIM_COUNT_THRESHOLD: int = 3

    # ── ANALYTICS Service ─────────────────────────────────
    ANALYTICS_SERVICE_BASE_URL: str = "http://localhost:8081/api/analytics"
    ANALYTICS_SERVICE_TIMEOUT_SECONDS: int = 5

    # ── AWS S3 ────────────────────────────────────────────
    S3_ENABLED: bool = False
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "eu-west-1"
    S3_BUCKET: str = "fraudly-resources"

    # ── Upload local (dev) ────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    INGESTION_DB_PATH: str = "./data/ingestion.db"

    # ── Security ───────────────────────────────────────────
    JWT_SECRET: str = ""
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()