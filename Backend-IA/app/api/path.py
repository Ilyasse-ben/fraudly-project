from fastapi import APIRouter, HTTPException
import time
import hashlib
from typing import Optional

from app.agents.path_agent import recommend_learning_path
from app.core.logger import get_logger
from app.db.ingestion_registry import record_audit_event
from app.schemas.path_schema import LearningPathResponse, StudentProfile, UUIDStr
from app.services.learning_profile_service import fetch_student_profile


logger = get_logger(__name__)
router = APIRouter()


@router.get("/recommend/{student_id}", response_model=LearningPathResponse)
async def recommend_path_by_student(student_id: UUIDStr, course_id: Optional[UUIDStr] = None):
    """Reconstruit un profil étudiant depuis Learning Service puis calcule le parcours."""
    started_at = time.time()
    payload_hash = hashlib.sha256(f"{student_id}|{course_id or ''}".encode("utf-8")).hexdigest()

    try:
        profile_data = fetch_student_profile(student_id, course_id)
        response = recommend_learning_path(StudentProfile.model_validate(profile_data))

        record_audit_event(
            event_type="path.recommend.by_student",
            endpoint=f"/path/recommend/{student_id}",
            status_code=200,
            success=True,
            duration_ms=int((time.time() - started_at) * 1000),
            provider=response.provider,
            fallback_used=False,
            course_id=response.course_id,
            payload_hash=payload_hash,
            details={
                "recommended_steps": len(response.recommended_steps),
                "source": "analytics-service",
            },
        )
        return response
    except ValueError as e:
        record_audit_event(
            event_type="path.recommend.by_student",
            endpoint=f"/path/recommend/{student_id}",
            status_code=400,
            success=False,
            duration_ms=int((time.time() - started_at) * 1000),
            payload_hash=payload_hash,
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        record_audit_event(
            event_type="path.recommend.by_student",
            endpoint=f"/path/recommend/{student_id}",
            status_code=502,
            success=False,
            duration_ms=int((time.time() - started_at) * 1000),
            payload_hash=payload_hash,
            error=str(e),
        )
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"[API/path] ERROR recommend by student: {e}")
        record_audit_event(
            event_type="path.recommend.by_student",
            endpoint=f"/path/recommend/{student_id}",
            status_code=500,
            success=False,
            duration_ms=int((time.time() - started_at) * 1000),
            payload_hash=payload_hash,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend", response_model=LearningPathResponse)
async def recommend_path(request: StudentProfile):
    """Retourne un parcours adapte a l'historique et aux lacunes de l'etudiant."""
    started_at = time.time()
    payload_hash = hashlib.sha256(
        f"{request.student_id}|{request.course_id}|{len(request.completed_chapters)}|{len(request.weak_topics)}".encode("utf-8")
    ).hexdigest()
    try:
        logger.info(
            "[API/path] student=%s course=%s completed=%d weak=%d",
            request.student_id,
            request.course_id,
            len(request.completed_chapters),
            len(request.weak_topics),
        )
        response = recommend_learning_path(request)
        record_audit_event(
            event_type="path.recommend",
            endpoint="/path/recommend",
            status_code=200,
            success=True,
            duration_ms=int((time.time() - started_at) * 1000),
            provider=response.provider,
            fallback_used=False,
            course_id=request.course_id,
            payload_hash=payload_hash,
            details={"recommended_steps": len(response.recommended_steps)},
        )
        return response
    except ValueError as e:
        record_audit_event(
            event_type="path.recommend",
            endpoint="/path/recommend",
            status_code=400,
            success=False,
            duration_ms=int((time.time() - started_at) * 1000),
            course_id=request.course_id,
            payload_hash=payload_hash,
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[API/path] ERROR: {e}")
        record_audit_event(
            event_type="path.recommend",
            endpoint="/path/recommend",
            status_code=500,
            success=False,
            duration_ms=int((time.time() - started_at) * 1000),
            course_id=request.course_id,
            payload_hash=payload_hash,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))