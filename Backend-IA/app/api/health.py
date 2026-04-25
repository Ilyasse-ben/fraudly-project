"""
Health check endpoint for RAG Service monitoring.
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.db.chroma_client import count_chunks, get_distinct_course_ids
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """Service liveness check."""
    return {
        "status": "ok",
        "service": "fraudly-rag",
        "version": "1.0.0",
    }


@router.get("/ready")
async def readiness_check():
    """Service readiness check — vérifie ChromaDB et embeddings."""
    try:
        total_chunks = count_chunks()
        courses = get_distinct_course_ids()
        return {
            "ready": True,
            "knowledge_base": {
                "total_chunks": total_chunks,
                "courses_indexed": len(courses),
            },
        }
    except Exception as e:
        logger.error(f"[Health] Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"ready": False, "error": str(e)},
        )
