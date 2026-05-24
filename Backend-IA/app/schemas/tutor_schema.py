from pydantic import BaseModel, Field
from typing import Annotated, Optional, List

UUID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
UUIDStr = Annotated[str, Field(pattern=UUID_PATTERN)]


class TutorAskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    course_id: Optional[UUIDStr] = None
    chapter_id: Optional[UUIDStr] = None
    student_id: Optional[UUIDStr] = None  
    session_id: Optional[str] = None      
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