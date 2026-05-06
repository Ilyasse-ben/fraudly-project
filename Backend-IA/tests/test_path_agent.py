import pathlib
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

_project_root = pathlib.Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from app.agents.path_agent import recommend_learning_path
from app.api.path import router as path_router
from app.schemas.path_schema import StudentProfile


STUDENT_A_ID = "550e8400-e29b-41d4-a716-446655440010"
STUDENT_B_ID = "550e8400-e29b-41d4-a716-446655440011"
COURSE_ID = "550e8400-e29b-41d4-a716-446655440020"

CHAPTER_INTRO = "550e8400-e29b-41d4-a716-446655440101"
CHAPTER_BASICS = "550e8400-e29b-41d4-a716-446655440102"
CHAPTER_DETECTION = "550e8400-e29b-41d4-a716-446655440103"
CHAPTER_FORENSICS = "550e8400-e29b-41d4-a716-446655440104"
CHAPTER_ETHICS = "550e8400-e29b-41d4-a716-446655440105"


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(path_router, prefix="/path")
    return TestClient(app)


def test_learning_path_differs_for_two_profiles():
    profile_a = StudentProfile(
        student_id=STUDENT_A_ID,
        course_id=COURSE_ID,
        completed_chapters=[CHAPTER_INTRO, CHAPTER_BASICS],
        scores={
            CHAPTER_INTRO: 0.92,
            CHAPTER_BASICS: 0.86,
            CHAPTER_DETECTION: 0.44,
            CHAPTER_FORENSICS: 0.58,
        },
        weak_topics=[CHAPTER_DETECTION],
    )
    profile_b = StudentProfile(
        student_id=STUDENT_B_ID,
        course_id=COURSE_ID,
        completed_chapters=[CHAPTER_INTRO],
        scores={
            CHAPTER_INTRO: 0.71,
            CHAPTER_BASICS: 0.49,
            CHAPTER_DETECTION: 0.83,
            CHAPTER_ETHICS: 0.56,
        },
        weak_topics=[CHAPTER_BASICS, CHAPTER_ETHICS],
    )

    path_a = recommend_learning_path(profile_a)
    path_b = recommend_learning_path(profile_b)

    assert path_a.recommended_steps[0].chapter_id != path_b.recommended_steps[0].chapter_id
    assert path_a.summary != path_b.summary
    assert path_a.provider == "heuristic"
    assert path_b.provider == "heuristic"


def test_learning_path_api_route_returns_payload():
    client = _client()
    response = client.post(
        "/path/recommend",
        json={
            "student_id": STUDENT_A_ID,
            "course_id": COURSE_ID,
            "completed_chapters": [CHAPTER_INTRO],
            "scores": {
                CHAPTER_INTRO: 0.9,
                CHAPTER_BASICS: 0.41,
                CHAPTER_DETECTION: 0.77,
            },
            "weak_topics": [CHAPTER_BASICS],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["student_id"] == STUDENT_A_ID
    assert payload["course_id"] == COURSE_ID
    assert payload["provider"] == "heuristic"
    assert payload["recommended_steps"][0]["priority"] == 1