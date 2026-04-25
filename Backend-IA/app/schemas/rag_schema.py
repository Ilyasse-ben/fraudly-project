from pydantic import BaseModel
from typing import List, Optional
from app.schemas.common import IngestStatus


# ── Ingestion ─────────────────────────────────────────────

class IngestResponse(BaseModel):
    resource_id: Optional[str] = None
    version: Optional[str] = None
    filename: str
    course_id: str
    chapter_id: str
    pages_processed: Optional[int] = None
    chunks_indexed: int
    status: IngestStatus
    idempotent_hit: bool = False
    message: Optional[str] = None


class IngestStatusResponse(BaseModel):
    resource_id: str
    version: str
    filename: str
    course_id: str
    chapter_id: str
    status: IngestStatus
    pages_processed: Optional[int] = None
    chunks_indexed: int
    message: Optional[str] = None
    created_at: str
    updated_at: str


# ── Retrieval ─────────────────────────────────────────────

class KnowledgeChunk(BaseModel):
    content: str
    course_id: str
    chapter_id: str
    source_file: str
    page: Optional[int] = None
    score: float


class KnowledgeSearchResponse(BaseModel):
    query: str
    chunks: List[KnowledgeChunk]
    total_found: int


class KnowledgeSearchRequest(BaseModel):
    query: str
    course_id: Optional[str] = None
    chapter_id: Optional[str] = None
    top_k: int = 5