from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator
from app.schemas.tutor_schema import ContextChunk, SourceChunk


QuestionType = Literal["qcm", "vrai_faux", "ouverte"]
DifficultyLevel = Literal["facile", "moyen", "difficile"]


class AssessmentGenerateRequest(BaseModel):
	topic: str = Field(..., min_length=3, max_length=2000)
	course_id: Optional[str] = None
	chapter_ids: Optional[List[str]] = None
	chapter_id: Optional[str] = None

	difficulty: DifficultyLevel = "moyen"
	total_questions: int = Field(default=10, ge=1, le=50)

	
	qcm_count: int = Field(default=0, ge=0, le=50)
	true_false_count: int = Field(default=0, ge=0, le=50)
	open_count: int = Field(default=0, ge=0, le=50)

	include_explanations: bool = True
	professor_instructions: Optional[str] = Field(default=None, max_length=2000)
	top_k: int = Field(default=8, ge=1, le=20)

	@model_validator(mode="before")
	@classmethod
	def _normalize_chapter_ids(cls, values):
		if not isinstance(values, dict):
			return values

		chapter_ids = values.get("chapter_ids")
		chapter_id = values.get("chapter_id")

		if chapter_ids is None and chapter_id:
			values["chapter_ids"] = [chapter_id]
		elif chapter_ids and chapter_id and chapter_id not in chapter_ids:
			values["chapter_ids"] = [*chapter_ids, chapter_id]

		return values



class QuestionChoice(BaseModel):
	label: str
	text: str
	is_correct: bool = False


class AssessmentQuestion(BaseModel):
	id: int
	type: QuestionType
	difficulty: DifficultyLevel
	question: str
	choices: List[QuestionChoice] = []
	correct_answer: str
	max_score: float = Field(default=1.0, gt=0, le=100)
	explanation: Optional[str] = None

	@model_validator(mode="before")
	@classmethod
	def _normalize_max_score(cls, values):
		if not isinstance(values, dict):
			return values

		# Compatibilite legacy: certains payloads peuvent envoyer "points".
		if "max_score" not in values and "points" in values:
			values["max_score"] = values["points"]

		return values


class AssessmentAuditTrail(BaseModel):
	provider: str
	fallback_used: bool
	retrieved_chunks: int
	prompt_chars: int
	generated_questions: int
	requested_difficulty: DifficultyLevel


class AssessmentGenerateResponse(BaseModel):
	topic: str
	difficulty: DifficultyLevel
	total_requested: int
	total_generated: int
	distribution: dict[str, int]
	questions: List[AssessmentQuestion]
	sources: List[SourceChunk]
	rag_context: List[ContextChunk]
	provider: str
	audit: AssessmentAuditTrail
