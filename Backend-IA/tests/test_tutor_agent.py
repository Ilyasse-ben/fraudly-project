from types import SimpleNamespace

from app.agents import tutor_agent
from app.schemas.tutor_schema import TutorAskRequest


class _FakeGraph:
    def invoke(self, _state):
        return {
            "question": "Qu'est-ce que la fraude documentaire ?",
            "course_id": "fraude_101",
            "chapter_id": "intro",
            "top_k": 3,
            "chunks": [
                SimpleNamespace(
                    source_file="intro.pdf",
                    page=2,
                    score=0.91,
                    content="La fraude documentaire est la falsification d'un document officiel.",
                )
            ],
            "prompt": "PROMPT CONTEXTE",
            "answer": "La fraude documentaire consiste a falsifier des documents [Source 1].",
            "provider": "groq",
            "fallback_used": False,
            "error": None,
        }


def test_ask_tutor_returns_visible_rag_context_and_audit(monkeypatch):
    monkeypatch.setattr(tutor_agent, "get_tutor_graph", lambda: _FakeGraph())

    req = TutorAskRequest(
        question="Qu'est-ce que la fraude documentaire ?",
        course_id="fraude_101",
        chapter_id="intro",
        top_k=3,
    )

    res = tutor_agent.ask_tutor(req)

    assert res.provider == "groq"
    assert res.chunks_used == 1
    assert len(res.sources) == 1
    assert len(res.rag_context) == 1
    assert "falsification" in res.rag_context[0].excerpt
    assert res.audit.provider == "groq"
    assert res.audit.fallback_used is False
    assert res.audit.retrieved_chunks == 1
    assert res.audit.prompt_chars == len("PROMPT CONTEXTE")
