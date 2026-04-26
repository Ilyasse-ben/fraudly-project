from pydantic import BaseModel, Field
from typing import Annotated, List, Optional
from app.schemas.common import IngestStatus

UUID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
UUIDStr = Annotated[str, Field(pattern=UUID_PATTERN)]


# ── Ingestion ─────────────────────────────────────────────

class IngestResponse(BaseModel):
    resource_id: Optional[UUIDStr] = None
    version: Optional[str] = None
    filename: str
    course_id: UUIDStr
    chapter_id: UUIDStr
    pages_processed: Optional[int] = None
    chunks_indexed: int
    status: IngestStatus
    idempotent_hit: bool = False
    message: Optional[str] = None


class IngestStatusResponse(BaseModel):
    resource_id: UUIDStr
    version: str
    filename: str
    course_id: UUIDStr
    chapter_id: UUIDStr
    status: IngestStatus
    pages_processed: Optional[int] = None
    chunks_indexed: int
    message: Optional[str] = None
    created_at: str
    updated_at: str


# ── Retrieval ─────────────────────────────────────────────

class KnowledgeChunk(BaseModel):
    content: str
    course_id: UUIDStr
    chapter_id: UUIDStr
    source_file: str
    page: Optional[int] = None
    score: float


class KnowledgeSearchResponse(BaseModel):
    query: str
    chunks: List[KnowledgeChunk]
    total_found: int


class KnowledgeSearchRequest(BaseModel):
    query: str
    course_id: Optional[UUIDStr] = None
    chapter_id: Optional[UUIDStr] = None
    top_k: int = 5