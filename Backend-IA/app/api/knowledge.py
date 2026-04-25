"""
Knowledge Base API — Retrieval endpoints pour les agents IA.
Endpoints principaux :
  - POST /search         : Recherche sémantique contextuelle
  - POST /ingest         : Indexation d'un document
  - GET /stats           : Statistiques KB
  - GET /courses         : Liste des cours indexés
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Body
from typing import Optional, List
import hashlib
import uuid
import time

from app.core.logger import get_logger
from app.schemas.common import DocumentType
from app.schemas.rag_schema import (
    KnowledgeSearchResponse,
    IngestResponse,
    IngestStatusResponse,
    KnowledgeSearchRequest,
)
from app.services.rag_service import search, ingest_file, ingest_bytes, get_kb_stats
from app.db.chroma_client import get_distinct_course_ids
from app.db.ingestion_registry import get_ingestion_job, upsert_ingestion_job, record_audit_event
from app.schemas.common import IngestStatus

logger = get_logger(__name__)

router = APIRouter()


# ─────────────────────────────────────────────────────────
# SEARCH
# ─────────────────────────────────────────────────────────

@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    query: Optional[str] = None,
    course_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    top_k: int = 5,
    payload: Optional[KnowledgeSearchRequest] = Body(default=None),
):
    """
    Recherche sémantique contextuelle dans la Knowledge Base.
    
    Args:
        query: Question ou requête en langage naturel
        course_id: Optionnel — filtre par cours
        chapter_id: Optionnel — filtre par chapitre (requiert course_id)
        top_k: Nombre de chunks à retourner (max 20)
    
    Returns:
        Liste de chunks pertinents avec scores de similarité
        et métadonnées (source, page, cours, chapitre)
    """
    # Supporte 2 formats:
    # 1) JSON body: {"query": "...", "course_id": "...", "top_k": 5}
    # 2) Query params: /knowledge/search?query=...&course_id=...&top_k=5
    if payload is not None:
        query = payload.query
        course_id = payload.course_id
        chapter_id = payload.chapter_id
        top_k = payload.top_k

    started_at = time.time()

    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="La requête ne peut pas être vide")
    
    if top_k < 1 or top_k > 20:
        raise HTTPException(status_code=400, detail="top_k doit être entre 1 et 20")
    
    try:
        payload_hash = hashlib.sha256(query.strip().encode("utf-8")).hexdigest() if query else None
        logger.info(f"[API] SEARCH → query='{query[:40]}' course={course_id} top_k={top_k}")
        result = search(
            query=query,
            course_id=course_id,
            chapter_id=chapter_id,
            top_k=top_k,
        )
        record_audit_event(
            event_type="knowledge.search",
            endpoint="/knowledge/search",
            status_code=200,
            success=True,
            duration_ms=int((time.time() - started_at) * 1000),
            course_id=course_id,
            chapter_id=chapter_id,
            payload_hash=payload_hash,
            details={
                "top_k": top_k,
                "total_found": result.total_found,
            },
        )
        return result
    except ValueError as e:
        record_audit_event(
            event_type="knowledge.search",
            endpoint="/knowledge/search",
            status_code=400,
            success=False,
            duration_ms=int((time.time() - started_at) * 1000),
            course_id=course_id,
            chapter_id=chapter_id,
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[API] SEARCH ERROR: {e}")
        record_audit_event(
            event_type="knowledge.search",
            endpoint="/knowledge/search",
            status_code=500,
            success=False,
            duration_ms=int((time.time() - started_at) * 1000),
            course_id=course_id,
            chapter_id=chapter_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Erreur lors de la recherche")


# ─────────────────────────────────────────────────────────
# INGEST
# ─────────────────────────────────────────────────────────

@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    course_id: str = Form(...),
    chapter_id: str = Form(...),
    resource_id: Optional[str] = Form(default=None),
    version: str = Form(default="v1"),
):
    """
    Ingère un document PDF/DOCX/PPTX dans la Knowledge Base.
    Déclenche automatiquement : extraction → chunking → embedding → indexation.
    
    Args:
        file: Fichier à ingérer (PDF, DOCX, PPTX)
        course_id: ID du cours
        chapter_id: ID du chapitre
    
    Returns:
        Statistiques d'ingestion (pages traitées, chunks indexés, status)
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Fichier manquant")
    
    # Validation extension
    allowed_exts = ("pdf", "docx", "pptx", "doc")
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté. Formats acceptés : {', '.join(allowed_exts)}"
        )
    
    # Map extension to DocumentType
    ext_to_type = {
        "pdf": DocumentType.PDF,
        "docx": DocumentType.DOCX,
        "doc": DocumentType.DOCX,
        "pptx": DocumentType.PPTX,
    }
    doc_type = ext_to_type[file_ext]
    started_at = time.time()
    
    try:
        # Lire le fichier uploadé
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Le fichier est vide")

        content_hash = hashlib.sha256(file_content).hexdigest()
        resolved_resource_id = resource_id or str(uuid.uuid4())

        existing = get_ingestion_job(resolved_resource_id, version)
        if existing:
            if existing["content_hash"] == content_hash and existing["status"] in {
                IngestStatus.OK.value,
                IngestStatus.EMPTY.value,
            }:
                logger.info(
                    f"[API] INGEST idempotent hit → resource_id={resolved_resource_id} version={version}"
                )
                record_audit_event(
                    event_type="knowledge.ingest",
                    endpoint="/knowledge/ingest",
                    status_code=200,
                    success=True,
                    duration_ms=int((time.time() - started_at) * 1000),
                    resource_id=resolved_resource_id,
                    version=version,
                    course_id=course_id,
                    chapter_id=chapter_id,
                    payload_hash=content_hash,
                    details={
                        "idempotent_hit": True,
                        "chunks_indexed": existing["chunks_indexed"],
                    },
                )
                return IngestResponse(
                    resource_id=resolved_resource_id,
                    version=version,
                    filename=existing["filename"],
                    course_id=existing["course_id"],
                    chapter_id=existing["chapter_id"],
                    pages_processed=existing["pages_processed"],
                    chunks_indexed=existing["chunks_indexed"],
                    status=IngestStatus(existing["status"]),
                    idempotent_hit=True,
                    message="Contenu déjà indexé pour cette resource/version.",
                )

            if existing["content_hash"] != content_hash:
                record_audit_event(
                    event_type="knowledge.ingest",
                    endpoint="/knowledge/ingest",
                    status_code=409,
                    success=False,
                    duration_ms=int((time.time() - started_at) * 1000),
                    resource_id=resolved_resource_id,
                    version=version,
                    course_id=course_id,
                    chapter_id=chapter_id,
                    payload_hash=content_hash,
                    error="resource_id/version deja utilisee avec un contenu different",
                )
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "resource_id/version déjà utilisée avec un contenu différent. "
                        "Incrémentez version (ex: v2)."
                    ),
                )
        
        logger.info(
            f"[API] INGEST → {file.filename} "
            f"({len(file_content)} bytes) course={course_id} chapter={chapter_id}"
        )
        
        result = ingest_bytes(
            file_bytes=file_content,
            filename=file.filename,
            course_id=course_id,
            chapter_id=chapter_id,
            doc_type=doc_type,
        )

        upsert_ingestion_job(
            resource_id=resolved_resource_id,
            version=version,
            filename=file.filename,
            course_id=course_id,
            chapter_id=chapter_id,
            content_hash=content_hash,
            status=result.status.value,
            pages_processed=result.pages_processed,
            chunks_indexed=result.chunks_indexed,
            message=result.message,
        )
        
        logger.info(f"[API] INGEST result: {result.chunks_indexed} chunks, status={result.status}")
        record_audit_event(
            event_type="knowledge.ingest",
            endpoint="/knowledge/ingest",
            status_code=200,
            success=result.status in {IngestStatus.OK, IngestStatus.EMPTY},
            duration_ms=int((time.time() - started_at) * 1000),
            resource_id=resolved_resource_id,
            version=version,
            course_id=course_id,
            chapter_id=chapter_id,
            payload_hash=content_hash,
            details={
                "idempotent_hit": False,
                "chunks_indexed": result.chunks_indexed,
                "pages_processed": result.pages_processed,
                "ingest_status": result.status.value,
            },
            error=result.message if result.status == IngestStatus.ERROR else None,
        )
        return IngestResponse(
            resource_id=resolved_resource_id,
            version=version,
            filename=result.filename,
            course_id=result.course_id,
            chapter_id=result.chapter_id,
            pages_processed=result.pages_processed,
            chunks_indexed=result.chunks_indexed,
            status=result.status,
            idempotent_hit=False,
            message=result.message,
        )
        
    except ValueError as e:
        record_audit_event(
            event_type="knowledge.ingest",
            endpoint="/knowledge/ingest",
            status_code=400,
            success=False,
            duration_ms=int((time.time() - started_at) * 1000),
            course_id=course_id,
            chapter_id=chapter_id,
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        if e.status_code != 409:
            record_audit_event(
                event_type="knowledge.ingest",
                endpoint="/knowledge/ingest",
                status_code=e.status_code,
                success=False,
                duration_ms=int((time.time() - started_at) * 1000),
                course_id=course_id,
                chapter_id=chapter_id,
                error=str(e.detail),
            )
        raise
    except Exception as e:
        logger.error(f"[API] INGEST ERROR: {e}")
        record_audit_event(
            event_type="knowledge.ingest",
            endpoint="/knowledge/ingest",
            status_code=500,
            success=False,
            duration_ms=int((time.time() - started_at) * 1000),
            course_id=course_id,
            chapter_id=chapter_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Erreur lors de l'ingestion")


@router.get("/ingest/status/{resource_id}", response_model=IngestStatusResponse)
async def get_ingest_status(resource_id: str, version: str = "v1"):
    """
    Retourne le statut d'indexation d'une ressource par resource_id/version.
    """
    job = get_ingestion_job(resource_id, version)
    if not job:
        raise HTTPException(status_code=404, detail="Aucun job d'ingestion trouvé")

    return IngestStatusResponse(
        resource_id=job["resource_id"],
        version=job["version"],
        filename=job["filename"],
        course_id=job["course_id"],
        chapter_id=job["chapter_id"],
        status=IngestStatus(job["status"]),
        pages_processed=job["pages_processed"],
        chunks_indexed=job["chunks_indexed"],
        message=job["message"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
    )


# ─────────────────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats():
    """
    Retourne les statistiques de la Knowledge Base.
    Utile pour monitoring et debug.
    """
    try:
        stats = get_kb_stats()
        return {
            "total_chunks": stats["total_chunks"],
            "collection_name": stats["collection_name"],
            "courses_indexed": stats["courses_indexed"],
        }
    except Exception as e:
        logger.error(f"[API] STATS ERROR: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des stats")


@router.get("/courses", response_model=List[str])
async def list_courses():
    """
    Retourne la liste des cours actuellement indexés dans la KB.
    Utile pour le frontend et le filtrage dans les recherches.
    """
    try:
        return get_distinct_course_ids()
    except Exception as e:
        logger.error(f"[API] LIST_COURSES ERROR: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des cours")
