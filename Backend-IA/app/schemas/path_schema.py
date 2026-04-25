from pydantic import BaseModel, Field
from typing import Dict, List


class StudentProfile(BaseModel):
    student_id: str
    course_id: str
    completed_chapters: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)  # {"chapter_1": 0.85, "chapter_2": 0.40}
    weak_topics: List[str] = Field(default_factory=list)


class RecommendedStep(BaseModel):
    chapter_id: str
    reason: str
    priority: int              # 1 = urgent, 2 = normal, 3 = optionnel


class LearningPathResponse(BaseModel):
    student_id: str
    course_id: str
    recommended_steps: List[RecommendedStep]
    summary: str
    provider: str