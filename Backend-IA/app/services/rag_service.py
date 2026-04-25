"""
RAG Service — orchestration complète ingestion + retrieval.
Optimisé pour stabilité + logs + performance IA-2.
"""

import os
import tempfile
import time
import uuid
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logger import get_logger
from app.db.chroma_client import (
    format_dimension_mismatch_error,
    get_collection,
    get_distinct_course_ids,
    is_dimension_mismatch_error,
    reset_collection,
)
from app.schemas.common import DocumentType, IngestStatus
from app.schemas.rag_schema import IngestResponse, KnowledgeChunk, KnowledgeSearchResponse
from app.services.chunking_service import chunk_pages
from app.services.document_loader import load_document
from app.services.embedding_service import embed_chunks, embed_query

logger = get_logger(__name__)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
EMBEDDING_BATCH_SIZE = 128
CHROMA_BATCH_SIZE = 64
# Limite de caractères injectés dans le prompt RAG pour éviter de dépasser
# la fenêtre de contexte du LLM et maîtriser les coûts API.
# À 800 chars/chunk × 5 chunks = 4 000 chars ≈ ~1 000 tokens → marge confortable.
MAX_CONTEXT_CHARS = 12_000


# ─────────────────────────────────────────────
# INGESTION
# ─────────────────────────────────────────────

def ingest_file(
    file_path: str,
    filename: str,
    course_id: str,
    chapter_id: str,
    doc_type: DocumentType,
) -> IngestResponse:
    """
    Pipeline complet :
    file → loader → chunk → embedding → ChromaDB
    """
    start_time = time.time()
    collection = get_collection()

    try:
        logger.info(f"[RAG] INGEST START → {filename}")

        pages = load_document(file_path, doc_type)
        if not pages:
            return IngestResponse(
                filename=filename,
                course_id=course_id,
                chapter_id=chapter_id,
                chunks_indexed=0,
                status=IngestStatus.EMPTY,
                message="Aucun texte extractible.",
            )

        logger.info(f"[RAG] Pages extraites: {len(pages)}")

        chunks = chunk_pages(pages, course_id, chapter_id, filename)
        if not chunks:
            return IngestResponse(
                filename=filename,
                course_id=course_id,
                chapter_id=chapter_id,
                chunks_indexed=0,
                status=IngestStatus.EMPTY,
            )

        texts = [c["text"] for c in chunks]
        logger.info(f"[RAG] Chunks générés: {len(texts)}")

        logger.info(f"[Embedding] START → {len(texts)} chunks")
        embeddings = []
        for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[i : i + EMBEDDING_BATCH_SIZE]
            embeddings.extend(embed_chunks(batch))
        logger.info(f"[Embedding] DONE → {len(embeddings)} embeddings")

        ids = [
            f"{course_id}_{chapter_id}_{i}_{uuid.uuid4().hex[:8]}"
            for i in range(len(chunks))
        ]

        logger.info(f"[RAG] Indexation ChromaDB → {len(ids)} chunks...")
        t0 = time.time()

        def _index_into(target_collection) -> None:
            for i in range(0, len(ids), CHROMA_BATCH_SIZE):
                target_collection.add(
                    ids=ids[i : i + CHROMA_BATCH_SIZE],
                    embeddings=embeddings[i : i + CHROMA_BATCH_SIZE],
                    documents=texts[i : i + CHROMA_BATCH_SIZE],
                    metadatas=[c["metadata"] for c in chunks[i : i + CHROMA_BATCH_SIZE]],
                )

        try:
            _index_into(collection)
        except Exception as e:
            if settings.CHROMA_AUTO_RESET_ON_DIMENSION_MISMATCH and is_dimension_mismatch_error(e):
                logger.warning(
                    f"[RAG] {format_dimension_mismatch_error(e)} → reset de la collection et réindexation."
                )
                reset_collection()
                collection = get_collection()
                _index_into(collection)
            else:
                raise

        logger.info(f"[RAG] Indexation terminée en {time.time() - t0:.2f}s")
        duration = time.time() - start_time
        logger.info(
            f"[RAG] ✓ {filename} | {len(pages)} pages | {len(chunks)} chunks | {duration:.2f}s"
        )

        return IngestResponse(
            filename=filename,
            course_id=course_id,
            chapter_id=chapter_id,
            pages_processed=len(pages),
            chunks_indexed=len(chunks),
            status=IngestStatus.OK,
        )

    except Exception as e:
        logger.error(f"[RAG] ERROR ingestion {filename}: {e}")
        return IngestResponse(
            filename=filename,
            course_id=course_id,
            chapter_id=chapter_id,
            chunks_indexed=0,
            status=IngestStatus.ERROR,
            message=str(e),
        )


# ─────────────────────────────────────────────
# INGEST BYTES
# ─────────────────────────────────────────────

def ingest_bytes(
    file_bytes: bytes,
    filename: str,
    course_id: str,
    chapter_id: str,
    doc_type: DocumentType,
) -> IngestResponse:
    """
    FIX : tmp_path initialisé à None avant le bloc with.
    Avant : si NamedTemporaryFile levait une exception avant d'assigner tmp_path,
    le finally plantait avec NameError sur os.unlink(tmp_path).
    Après  : on vérifie l'existence du fichier avant de le supprimer.
    """
    tmp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{doc_type.value}") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        return ingest_file(tmp_path, filename, course_id, chapter_id, doc_type)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError as e:
                logger.warning(f"[RAG] Impossible de supprimer le fichier temporaire {tmp_path}: {e}")


# ─────────────────────────────────────────────
# SEARCH
# ─────────────────────────────────────────────

def search(
    query: str,
    course_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    chapter_ids: Optional[List[str]] = None,
    top_k: int = 5,
) -> KnowledgeSearchResponse:
    """
    Recherche sémantique dans ChromaDB.
    Retourne toujours un KnowledgeSearchResponse valide (jamais d'exception propagée).
    """
    collection = get_collection()
    n_total = collection.count()

    if n_total == 0:
        return KnowledgeSearchResponse(query=query, chunks=[], total_found=0)

    selected_chapter_ids: List[str] = []
    if chapter_ids:
        for selected_chapter_id in chapter_ids:
            if selected_chapter_id and selected_chapter_id not in selected_chapter_ids:
                selected_chapter_ids.append(selected_chapter_id)
    elif chapter_id:
        selected_chapter_ids.append(chapter_id)

    def _build_where(target_chapter_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if course_id and target_chapter_id:
            return {"$and": [{"course_id": course_id}, {"chapter_id": target_chapter_id}]}
        if course_id:
            return {"course_id": course_id}
        if target_chapter_id:
            return {"chapter_id": target_chapter_id}
        return None

    def _extract_chunks(results: Dict[str, Any]) -> List[KnowledgeChunk]:
        if not results or not results.get("documents"):
            return []

        return [
            KnowledgeChunk(
                content=doc,
                course_id=meta.get("course_id", ""),
                chapter_id=meta.get("chapter_id", ""),
                source_file=meta.get("source_file", ""),
                page=meta.get("page"),
                score=round(max(0.0, 1.0 - float(dist)), 4),
            )
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]

    try:
        query_embedding = [embed_query(query)]

        if not selected_chapter_ids:
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=min(top_k, n_total),
                where=_build_where(None),
                include=["documents", "metadatas", "distances"],
            )
            chunks = _extract_chunks(results)
        else:
            chunks = []
            for selected_chapter_id in selected_chapter_ids:
                results = collection.query(
                    query_embeddings=query_embedding,
                    n_results=min(top_k, n_total),
                    where=_build_where(selected_chapter_id),
                    include=["documents", "metadatas", "distances"],
                )
                chunks.extend(_extract_chunks(results))

            deduped_chunks = []
            seen = set()
            for chunk in sorted(chunks, key=lambda item: item.score, reverse=True):
                signature = (chunk.content, chunk.course_id, chunk.chapter_id, chunk.source_file, chunk.page)
                if signature in seen:
                    continue
                seen.add(signature)
                deduped_chunks.append(chunk)
            chunks = deduped_chunks[:top_k]

        if not chunks:
            return KnowledgeSearchResponse(query=query, chunks=[], total_found=0)

        logger.info(f"[RAG] SEARCH '{query[:40]}' → {len(chunks)} chunks")
        return KnowledgeSearchResponse(query=query, chunks=chunks, total_found=len(chunks))

    except Exception as e:
        if settings.CHROMA_AUTO_RESET_ON_DIMENSION_MISMATCH and is_dimension_mismatch_error(e):
            logger.warning(
                f"[RAG] {format_dimension_mismatch_error(e)} → reset de la collection avant recherche."
            )
            reset_collection()
            return KnowledgeSearchResponse(query=query, chunks=[], total_found=0)

        logger.error(f"[RAG] SEARCH ERROR: {e}")
        return KnowledgeSearchResponse(query=query, chunks=[], total_found=0)


# ─────────────────────────────────────────────
# PROMPT
# ─────────────────────────────────────────────

def build_rag_prompt(question: str, chunks: List[KnowledgeChunk]) -> str:
    """
    Construit le prompt RAG injecté dans le LLM.
    FIX : troncature du contexte à MAX_CONTEXT_CHARS pour éviter de dépasser
    la fenêtre de contexte du LLM et maîtriser les coûts API.
    Les chunks sont déjà triés par score décroissant (meilleurs en premier).
    """
    parts: List[str] = []
    total_chars = 0

    for i, c in enumerate(chunks, 1):
        entry = (
            f"[Source {i}] {c.source_file} (page {c.page}) | score {c.score}\n"
            f"{c.content}"
        )
        if total_chars + len(entry) > MAX_CONTEXT_CHARS:
            logger.warning(
                f"[RAG] Contexte tronqué à {total_chars} chars "
                f"({i - 1}/{len(chunks)} chunks) pour respecter MAX_CONTEXT_CHARS={MAX_CONTEXT_CHARS}"
            )
            break
        parts.append(entry)
        total_chars += len(entry)

    context = "\n\n".join(parts) if parts else "Aucun document pertinent trouvé."

    return (
        "Tu es un assistant pédagogique expert.\n\n"
        "RÈGLES STRICTES:\n"
        "- Utilise uniquement le CONTEXTE fourni\n"
        "- Ne pas inventer d'informations absentes du contexte\n"
        "- Cite les sources ([Source N]) dans ta réponse\n\n"
        f"CONTEXTE:\n{context}\n\n"
        f"QUESTION:\n{question}\n\n"
        "RÉPONSE:"
    )


# ─────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────

def get_kb_stats() -> Dict[str, Any]:
    col = get_collection()
    return {
        "total_chunks": col.count(),
        "collection_name": col.name,
        "courses_indexed": get_distinct_course_ids(),
    }
