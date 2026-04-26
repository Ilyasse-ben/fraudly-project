import asyncio
import json
import pathlib
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

_project_root = pathlib.Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

_fixtures_root = pathlib.Path(__file__).resolve().parent / "fixtures"
_real_chapter_path = _fixtures_root / "assessment_real_chapter.json"

from app.api.assessment import assessment_generate, router as assessment_router
from app.agents import assessment_agent
from app.schemas.assessment_schema import AssessmentGenerateRequest


with _real_chapter_path.open("r", encoding="utf-8") as chapter_file:
    REAL_CHAPTER = json.load(chapter_file)


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(assessment_router, prefix="/assessment")
    return TestClient(app)


def test_assessment_generate_full_flow(monkeypatch):
    chunks = [
        SimpleNamespace(
            content=REAL_CHAPTER["content"],
            course_id=REAL_CHAPTER["course_id"],
            chapter_id=REAL_CHAPTER["chapter_id"],
            source_file=REAL_CHAPTER["source_file"],
            page=REAL_CHAPTER["page"],
            score=0.93,
        )
    ]

    llm_payload = {
        "questions": [
            {
                "id": 1,
                "type": "qcm",
                "difficulty": "moyen",
                "question": "Quelle est la définition principale de la fraude documentaire ?",
                "choices": [
                    {"label": "A", "text": "Une falsification de document", "is_correct": True},
                    {"label": "B", "text": "Une erreur de saisie", "is_correct": False},
                    {"label": "C", "text": "Un contrôle qualité", "is_correct": False},
                    {"label": "D", "text": "Une archive numérique", "is_correct": False},
                ],
                "correct_answer": "A",
                "max_score": 2,
                "explanation": "La fraude documentaire consiste à falsifier un document officiel.",
            },
            {
                "id": 2,
                "type": "vrai_faux",
                "difficulty": "facile",
                "question": "Les métadonnées peuvent aider à détecter une fraude documentaire.",
                "choices": [],
                "correct_answer": "Vrai",
                "max_score": 1,
                "explanation": "Les métadonnées font partie des signaux de détection.",
            },
            {
                "id": 3,
                "type": "ouverte",
                "difficulty": "difficile",
                "question": "Citez un indice technique utile pour détecter un faux document.",
                "choices": [],
                "correct_answer": "Analyse des métadonnées ou incohérence des polices.",
                "max_score": 3,
                "explanation": "Les indices techniques doivent provenir du contexte fourni.",
            },
        ]
    }

    monkeypatch.setattr(
        assessment_agent,
        "search",
        lambda **kwargs: SimpleNamespace(chunks=chunks),
    )
    monkeypatch.setattr(
        assessment_agent,
        "invoke_with_fallback",
        lambda prompt: SimpleNamespace(
            answer=json.dumps(llm_payload, ensure_ascii=False),
            provider="groq",
            fallback_used=False,
            error=None,
        ),
    )
    mock_audit = MagicMock()
    monkeypatch.setattr("app.api.assessment.record_audit_event", mock_audit)

    client = _client()
    response = client.post(
        "/assessment/generate",
        json={
            "topic": REAL_CHAPTER["title"],
            "course_id": REAL_CHAPTER["course_id"],
            "chapter_id": REAL_CHAPTER["chapter_id"],
            "difficulty": "moyen",
            "total_questions": 3,
            "qcm_count": 1,
            "true_false_count": 1,
            "open_count": 1,
            "include_explanations": True,
            "professor_instructions": "Mets l'accent sur les indices techniques.",
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["topic"] == REAL_CHAPTER["title"]
    assert payload["difficulty"] == "moyen"
    assert payload["total_requested"] == 3
    assert payload["total_generated"] == 3
    assert payload["distribution"] == {"qcm": 1, "vrai_faux": 1, "ouverte": 1}
    assert payload["provider"] == "groq"
    assert payload["audit"]["generated_questions"] == 3
    assert payload["audit"]["retrieved_chunks"] == 1
    assert payload["questions"][0]["choices"][0]["is_correct"] is True
    assert payload["questions"][2]["max_score"] == 3
    mock_audit.assert_called_once()


def test_assessment_generate_with_real_chapter_id(monkeypatch):
    chunks = [
        SimpleNamespace(
            content=REAL_CHAPTER["content"],
            course_id=REAL_CHAPTER["course_id"],
            chapter_id=REAL_CHAPTER["chapter_id"],
            source_file=REAL_CHAPTER["source_file"],
            page=REAL_CHAPTER["page"],
            score=0.91,
        )
    ]

    llm_payload = {
        "questions": [
            {
                "id": 1,
                "type": "qcm",
                "difficulty": "moyen",
                "question": "Quelle technique aide a detecter une fraude documentaire ?",
                "choices": [
                    {"label": "A", "text": "L'analyse des metadonnees", "is_correct": True},
                    {"label": "B", "text": "Le tri manuel aléatoire", "is_correct": False},
                    {"label": "C", "text": "La suppression des pages", "is_correct": False},
                    {"label": "D", "text": "La compression du fichier", "is_correct": False},
                ],
                "correct_answer": "A",
                "max_score": 2,
                "explanation": "Les metadonnees et les incoherences sont des indices utiles.",
            }
        ]
    }

    monkeypatch.setattr(
        assessment_agent,
        "search",
        lambda **kwargs: SimpleNamespace(chunks=chunks),
    )
    monkeypatch.setattr(
        assessment_agent,
        "invoke_with_fallback",
        lambda prompt: SimpleNamespace(
            answer=json.dumps(llm_payload, ensure_ascii=False),
            provider="groq",
            fallback_used=False,
            error=None,
        ),
    )
    mock_audit = MagicMock()
    monkeypatch.setattr("app.api.assessment.record_audit_event", mock_audit)

    request = AssessmentGenerateRequest.model_construct(
        topic=REAL_CHAPTER["title"],
        course_id=REAL_CHAPTER["course_id"],
        chapter_id=REAL_CHAPTER["chapter_id"],
        chapter_ids=[REAL_CHAPTER["chapter_id"]],
        difficulty="moyen",
        total_questions=1,
        qcm_count=1,
        true_false_count=0,
        open_count=0,
        include_explanations=True,
        professor_instructions="Utilise le vocabulaire du chapitre fourni.",
        top_k=1,
    )

    response = asyncio.run(assessment_generate(request))

    assert response.topic == REAL_CHAPTER["title"]
    assert response.questions[0].question == "Quelle technique aide a detecter une fraude documentaire ?"
    assert response.audit.retrieved_chunks == 1
    assert response.rag_context[0].source_file == REAL_CHAPTER["source_file"]
    mock_audit.assert_called_once()
