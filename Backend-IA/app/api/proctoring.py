"""
Proctoring API — Statut du pipeline de détection de collusion.
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.logger import get_logger
from app.core.config import settings
from app.services.collusion_detector import get_collusion_consumer

logger = get_logger(__name__)

router = APIRouter()


class ProctorStatusResponse(BaseModel):
    """Statut du service de proctoring."""
    kafka_enabled: bool
    kafka_bootstrap_servers: str
    exam_submitted_topic: str
    fraud_alerts_topic: str
    collusion_consumer_running: bool
    collusion_model: str
    similarity_threshold: float


@router.get("/status", response_model=ProctorStatusResponse)
async def get_proctor_status() -> ProctorStatusResponse:
    """Retourne le statut du service de proctoring."""
    consumer = get_collusion_consumer()
    
    return ProctorStatusResponse(
        kafka_enabled=settings.KAFKA_ENABLED,
        kafka_bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        exam_submitted_topic=settings.KAFKA_TOPIC_EXAM_SUBMITTED,
        fraud_alerts_topic=settings.KAFKA_TOPIC_FRAUD_ALERTS,
        collusion_consumer_running=consumer._running if consumer else False,
        collusion_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        similarity_threshold=0.85,
    )


