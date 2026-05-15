from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uuid
import asyncio

from app.core.config import settings
from app.core.logger import get_logger, set_request_id, reset_request_id
from app.db.chroma_client import init_chroma
from app.services.embedding_service import warm_up_model
from app.services.collusion_detector import run_collusion_consumer_loop, stop_collusion_consumer
from app.services.exam_scorer_service import run_exam_scorer_loop, stop_exam_scorer_consumer
from app.kafka.consumer import run_resource_consumer_loop, stop_consumer
from app.api.knowledge import router as knowledge_router
from app.api.health import router as health_router
from app.api.tutor import router as tutor_router
from app.api.assessment import router as assessment_router
from app.api.path import router as path_router
from app.api.proctoring import router as proctoring_router
from app.middleware.internal_auth import InternalAuthMiddleware


logger = get_logger(__name__)

# ── Background tasks ──────────────────────────────────
_collusion_task: asyncio.Task = None
_exam_scorer_task: asyncio.Task = None
_resource_consumer_task: asyncio.Task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────
    global _collusion_task, _exam_scorer_task, _resource_consumer_task
    
    logger.info("Starting Fraudly RAG Service...")
    init_chroma()
    if settings.EMBEDDING_WARMUP_ON_STARTUP:
        warm_up_model()
    else:
        logger.info("Embedding warmup désactivé au startup (chargement lazy au premier appel).")
    
    #Lance les consumers Kafka
    if settings.KAFKA_ENABLED:
        logger.info("[Collusion] Démarrage du consumer en arrière-plan...")
        _collusion_task = asyncio.create_task(run_collusion_consumer_loop())
        logger.info("[ExamScorer] Démarrage du consumer en arrière-plan...")
        _exam_scorer_task = asyncio.create_task(run_exam_scorer_loop())
        logger.info("[ResourceConsumer] Démarrage du consumer en arrière-plan...")
        _resource_consumer_task = asyncio.create_task(run_resource_consumer_loop())
    else:
        logger.info("[Collusion] Kafka désactivé, consumer non lancé")
        logger.info("[ExamScorer] Kafka désactivé, consumer non lancé")
        logger.info("[ResourceConsumer] Kafka désactivé, consumer non lancé")
    
    logger.info("RAG Service ready.")
    yield
    # ── Shutdown ─────────────────────────────────────────
    logger.info("Shutting down RAG Service...")
    
    # Arrête les consumers Kafka
    if _collusion_task and not _collusion_task.done():
        _collusion_task.cancel()
        try:
            await _collusion_task
        except asyncio.CancelledError:
            pass

    if _exam_scorer_task and not _exam_scorer_task.done():
        _exam_scorer_task.cancel()
        try:
            await _exam_scorer_task
        except asyncio.CancelledError:
            pass

    if _resource_consumer_task and not _resource_consumer_task.done():
        _resource_consumer_task.cancel()
        try:
            await _resource_consumer_task
        except asyncio.CancelledError:
            pass
    
    stop_collusion_consumer()
    stop_exam_scorer_consumer()
    stop_consumer()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Fraudly — RAG Knowledge Base Service",
    description=(
        "Pipeline RAG pour le Tutor Agent de Fraudly. "
        "Indexe les ressources pédagogiques (PDF, DOCX, PPTX) "
        "et expose le retrieval contextuel aux agents IA."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(InternalAuthMiddleware)



@app.middleware("http")
async def request_id_middleware(request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    token = set_request_id(request_id)
    try:
        response = await call_next(request)
    finally:
        reset_request_id(token)

    response.headers["X-Request-ID"] = request_id
    return response

app.include_router(health_router, tags=["Health"])
app.include_router(knowledge_router, prefix="/knowledge", tags=["Knowledge Base"])
app.include_router(tutor_router, prefix="/tutor", tags=["Tutor Agent"])
app.include_router(assessment_router, prefix="/assessment", tags=["Assessment Agent"])
app.include_router(path_router, prefix="/path", tags=["Learning Path Engine"])
app.include_router(proctoring_router, prefix="/proctoring", tags=["Proctoring"])
