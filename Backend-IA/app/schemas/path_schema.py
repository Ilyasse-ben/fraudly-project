from pydantic import BaseModel, Field
from typing import Annotated, Dict, List

UUID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
UUIDStr = Annotated[str, Field(pattern=UUID_PATTERN)]


class StudentProfile(BaseModel):
    student_id: UUIDStr
    course_id: UUIDStr
    completed_chapters: List[UUIDStr] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)  # {"chapter_1": 0.85, "chapter_2": 0.40}
    weak_topics: List[str] = Field(default_factory=list)


class RecommendedStep(BaseModel):
    chapter_id: UUIDStr
    reason: str
    priority: int              # 1 = urgent, 2 = normal, 3 = optionnel


class LearningPathResponse(BaseModel):
    student_id: UUIDStr
    course_id: UUIDStr
    recommended_steps: List[RecommendedStep]
    summary: str
    provider: str