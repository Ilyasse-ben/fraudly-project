from fastapi import APIRouter, HTTPException
import time
import hashlib
from app.schemas.tutor_schema import TutorAskRequest, TutorAskResponse
from app.services.llm_router import invoke_with_fallback
from app.agents.tutor_agent import ask_tutor
from app.core.logger import get_logger
from app.db.ingestion_registry import record_audit_event
from app.kafka.producer import publish_event
from app.core.config import settings
from app.services.session_memory_service import (
    append_turn,
    build_session_context,
    get_recent_turns,
)
from app.services.tutor_monitor import detect_student_block
import uuid

logger = get_logger(__name__)
router = APIRouter()


@router.post("/ask", response_model=TutorAskResponse)
async def tutor_ask(request: TutorAskRequest):
    """
    Pose une question au Tutor Agent.
    Le contexte est récupéré depuis la Knowledge Base (RAG).
    """
    started_at = time.time()
    original_question = request.question
    payload_hash = hashlib.sha256(original_question.encode("utf-8")).hexdigest()
    # Générer session_id si absent
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        session_turns = get_recent_turns(session_id)
        session_context = build_session_context(session_turns)

        effective_question = original_question
        if session_context:
            effective_question = f"{original_question}\n\n{session_context}"

        effective_request = request.model_copy(
            update={
                "question": effective_question,
                "session_id": session_id,
            }
        )

        logger.info(f"[API/tutor] question='{original_question[:60]}'")
        response = ask_tutor(effective_request)
        response.question = original_question

        append_turn(session_id, original_question, response.answer)

        # Détecter un blocage probable dans la session tutor.
        if request.student_id:
            block_result = detect_student_block(session_id)
            if block_result.get("blocked"):
                block_event = {
                    "student_id": request.student_id,
                    "session_id": session_id,
                    "course_id": request.course_id,
                    "chapter_id": request.chapter_id,
                    "reason": block_result.get("reason"),
                    "details": block_result.get("details", {}),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                publish_event(settings.KAFKA_TOPIC_STUDENT_BLOCKED, block_event)
                logger.info(
                    "[API/tutor] Blocage détecté student=%s session=%s reason=%s",
                    request.student_id,
                    session_id,
                    block_result.get("reason"),
                )
        
        # Publier interaction sur Kafka
        if request.student_id:
            # Extraire le topic via LLM
            topic = await extract_topic_llm(
                request.question, 
                response.answer
            )
            
            publish_event("tutor.interaction_logged", {
                "student_id": request.student_id,
                "course_id": request.course_id,
                "chapter_id": request.chapter_id,
                "session_id": session_id,
                "question": original_question,
                "topic": topic,             
                "provider": response.provider,
                "fallback_used": response.audit.fallback_used,
                "chunks_used": response.chunks_used,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })

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
                "student_id": request.student_id,
                "session_id": session_id,
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

async def extract_topic_llm(question: str, answer: str) -> str:
    """Extrait le topic principal d'une interaction tutor via LLM."""
    try:
        prompt = f"""Extrais le topic principal de cette question pédagogique en 2-4 mots maximum.

        Question: {question}
        Réponse: {answer[:300]}

        Réponds UNIQUEMENT avec le topic, rien d'autre.
        Exemples: "complexité algorithmique", "tri fusion", "récursivité", "structures de données"
"""
        result = invoke_with_fallback(prompt)
        topic = (result.answer or "général").strip()
        # Nettoyer la réponse
        topic = topic.replace('"', '').replace("'", '').strip()
        return topic if topic else "général"
    except Exception:
        return "général"
