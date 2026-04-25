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


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(path_router, prefix="/path")
    return TestClient(app)


def test_learning_path_differs_for_two_profiles():
    profile_a = StudentProfile(
        student_id="student-a",
        course_id="fraud-101",
        completed_chapters=["intro", "basics"],
        scores={"intro": 0.92, "basics": 0.86, "detection": 0.44, "forensics": 0.58},
        weak_topics=["detection"],
    )
    profile_b = StudentProfile(
        student_id="student-b",
        course_id="fraud-101",
        completed_chapters=["intro"],
        scores={"intro": 0.71, "basics": 0.49, "detection": 0.83, "ethics": 0.56},
        weak_topics=["basics", "ethics"],
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
            "student_id": "student-a",
            "course_id": "fraud-101",
            "completed_chapters": ["intro"],
            "scores": {"intro": 0.9, "basics": 0.41, "detection": 0.77},
            "weak_topics": ["basics"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["student_id"] == "student-a"
    assert payload["course_id"] == "fraud-101"
    assert payload["provider"] == "heuristic"
    assert payload["recommended_steps"][0]["priority"] == 1