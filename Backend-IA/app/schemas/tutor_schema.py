from pydantic import BaseModel, Field
from typing import Optional, List


class TutorAskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    course_id: Optional[str] = None
    chapter_id: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)


class SourceChunk(BaseModel):
    source_file: str
    page: Optional[int] = None
    score: float


class ContextChunk(BaseModel):
    source_file: str
    page: Optional[int] = None
    score: float
    excerpt: str


class TutorAuditTrail(BaseModel):
    provider: str
    fallback_used: bool
    retrieved_chunks: int
    prompt_chars: int


class TutorAskResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceChunk]
    rag_context: List[ContextChunk]
    chunks_used: int
    provider: str  # "groq" ou "gemini"
    audit: TutorAuditTrail