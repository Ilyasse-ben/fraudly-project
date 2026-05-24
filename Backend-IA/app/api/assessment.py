from fastapi import APIRouter, HTTPException
import time
import hashlib

from app.agents.assessment_agent import generate_assessment
from app.core.logger import get_logger
from app.db.ingestion_registry import record_audit_event
from app.schemas.assessment_schema import AssessmentGenerateRequest, AssessmentGenerateResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("/generate", response_model=AssessmentGenerateResponse)
async def assessment_generate(request: AssessmentGenerateRequest):
	"""
	Génère une évaluation (QCM, Vrai/Faux, ouvertes) à partir du contexte RAG.
	La difficulté et la distribution sont configurables par le professeur.
	"""
	started_at = time.time()
	payload_hash = hashlib.sha256(request.topic.encode("utf-8")).hexdigest()
	chapter_id = request.chapter_id or (request.chapter_ids[0] if request.chapter_ids else None)
	chapter_ids = request.chapter_ids or ([request.chapter_id] if request.chapter_id else None)
	try:
		logger.info(
			"[API/assessment] "
			f"topic='{request.topic[:60]}' total={request.total_questions} difficulty={request.difficulty}"
		)
		response = generate_assessment(request)
		record_audit_event(
			event_type="assessment.generate",
			endpoint="/assessment/generate",
			status_code=200,
			success=True,
			duration_ms=int((time.time() - started_at) * 1000),
			provider=response.provider,
			fallback_used=response.audit.fallback_used,
			course_id=request.course_id,
			chapter_id=chapter_id,
			payload_hash=payload_hash,
			details={
				"retrieved_chunks": response.audit.retrieved_chunks,
				"generated_questions": response.audit.generated_questions,
				"chapter_ids": chapter_ids,
			},
		)
		return response
	except ValueError as e:
		record_audit_event(
			event_type="assessment.generate",
			endpoint="/assessment/generate",
			status_code=400,
			success=False,
			duration_ms=int((time.time() - started_at) * 1000),
			course_id=request.course_id,
			chapter_id=chapter_id,
			payload_hash=payload_hash,
			details={"chapter_ids": chapter_ids},
			error=str(e),
		)
		raise HTTPException(status_code=400, detail=str(e))
	except Exception as e:
		logger.error(f"[API/assessment] ERROR: {e}")
		record_audit_event(
			event_type="assessment.generate",
			endpoint="/assessment/generate",
			status_code=500,
			success=False,
			duration_ms=int((time.time() - started_at) * 1000),
			course_id=request.course_id,
			chapter_id=chapter_id,
			payload_hash=payload_hash,
			details={"chapter_ids": chapter_ids},
			error=str(e),
		)
		raise HTTPException(status_code=500, detail=str(e))
