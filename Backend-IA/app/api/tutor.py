from fastapi import APIRouter, HTTPException
import time
import hashlib
from app.schemas.tutor_schema import TutorAskRequest, TutorAskResponse
from app.agents.tutor_agent import ask_tutor
from app.core.logger import get_logger
from app.db.ingestion_registry import record_audit_event

logger = get_logger(__name__)
router = APIRouter()


@router.post("/ask", response_model=TutorAskResponse)
async def tutor_ask(request: TutorAskRequest):
    """
    Pose une question au Tutor Agent.
    Le contexte est récupéré depuis la Knowledge Base (RAG).
    """
    started_at = time.time()
    payload_hash = hashlib.sha256(request.question.encode("utf-8")).hexdigest()
    try:
        logger.info(f"[API/tutor] question='{request.question[:60]}'")
        response = ask_tutor(request)
        record_audit_event(
            event_type="tutor.ask",
            endpoint="/tutor/ask",
            status_code=200,
            success=True,
            duration_ms=int((time.time() - started_at) * 1000),
            provider=response.provider,
            fallback_used=response.audit.fallback_used,
            course_id=request.course_id,
            chapter_id=request.chapter_id,
            payload_hash=payload_hash,
            details={
                "retrieved_chunks": response.audit.retrieved_chunks,
                "chunks_used": response.chunks_used,
            },
        )
        return response
    except Exception as e:
        logger.error(f"[API/tutor] ERROR: {e}")
        record_audit_event(
            event_type="tutor.ask",
            endpoint="/tutor/ask",
            status_code=500,
            success=False,
            duration_ms=int((time.time() - started_at) * 1000),
            course_id=request.course_id,
            chapter_id=request.chapter_id,
            payload_hash=payload_hash,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))