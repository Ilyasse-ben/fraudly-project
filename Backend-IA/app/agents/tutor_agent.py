"""
Tutor Agent – RAG + LLM (Groq primary, Gemini fallback)
Architecture LangGraph : retrieve -> generate
"""

from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END

from app.core.logger import get_logger
from app.services.rag_service import search, build_rag_prompt
from app.services.llm_router import invoke_with_fallback
from app.schemas.rag_schema import KnowledgeChunk
from app.schemas.tutor_schema import (
    TutorAskRequest,
    TutorAskResponse,
    SourceChunk,
    ContextChunk,
    TutorAuditTrail,
)

logger = get_logger(__name__)


# State 

class TutorState(TypedDict):
    question: str
    course_id: Optional[str]
    chapter_id: Optional[str]
    top_k: int
    chunks: List[KnowledgeChunk]
    prompt: str
    answer: str
    provider: str
    fallback_used: bool
    error: Optional[str]


# Nodes 

def retrieve_node(state: TutorState) -> TutorState:
    """Recherche sémantique dans ChromaDB."""
    logger.info(f"[TutorAgent] RETRIEVE → '{state['question'][:50]}'")

    result = search(
        query=state["question"],
        course_id=state.get("course_id"),
        chapter_id=state.get("chapter_id"),
        top_k=state["top_k"],
    )

    prompt = build_rag_prompt(state["question"], result.chunks)

    logger.info(f"[TutorAgent] {len(result.chunks)} chunks récupérés")

    return {**state, "chunks": result.chunks, "prompt": prompt}


def generate_node(state: TutorState) -> TutorState:
    """Appel LLM avec fallback configure via .env."""

    if not state["chunks"]:
        logger.info("[TutorAgent] Aucun contexte trouve -> reponse de securite")
        return {
            **state,
            "answer": (
                "Je n'ai pas trouve de contenu pertinent dans la base de connaissances "
                "pour repondre avec certitude."
            ),
            "provider": "none",
            "fallback_used": False,
        }

    llm_result = invoke_with_fallback(state["prompt"])
    if llm_result.answer:
        return {
            **state,
            "answer": llm_result.answer,
            "provider": llm_result.provider,
            "fallback_used": llm_result.fallback_used,
        }

    return {
        **state,
        "answer": "Aucun LLM configuré. Veuillez contacter l'administrateur.",
        "provider": "none",
        "fallback_used": False,
        "error": llm_result.error,
    }


# Graph 

def build_tutor_graph() -> StateGraph:
    graph = StateGraph(TutorState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


_tutor_graph = None

def get_tutor_graph():
    global _tutor_graph
    if _tutor_graph is None:
        _tutor_graph = build_tutor_graph()
    return _tutor_graph


# Public API 

def ask_tutor(request: TutorAskRequest) -> TutorAskResponse:
    """Point d'entrée principal du Tutor Agent."""
    graph = get_tutor_graph()

    initial_state: TutorState = {
        "question": request.question,
        "course_id": request.course_id,
        "chapter_id": request.chapter_id,
        "top_k": request.top_k,
        "chunks": [],
        "prompt": "",
        "answer": "",
        "provider": "none",
        "fallback_used": False,
        "error": None,
    }

    final_state = graph.invoke(initial_state)

    sources = [
        SourceChunk(
            source_file=c.source_file,
            page=c.page,
            score=c.score,
        )
        for c in final_state["chunks"]
    ]

    rag_context = [
        ContextChunk(
            source_file=c.source_file,
            page=c.page,
            score=c.score,
            excerpt=(c.content[:300] + "...") if len(c.content) > 300 else c.content,
        )
        for c in final_state["chunks"]
    ]

    audit = TutorAuditTrail(
        provider=final_state["provider"],
        fallback_used=final_state["fallback_used"],
        retrieved_chunks=len(final_state["chunks"]),
        prompt_chars=len(final_state["prompt"]),
    )

    logger.info(
        "[TutorAgent][AUDIT] "
        f"provider={audit.provider} fallback={audit.fallback_used} "
        f"chunks={audit.retrieved_chunks} prompt_chars={audit.prompt_chars} "
        f"question='{request.question[:80]}'"
    )

    return TutorAskResponse(
        question=request.question,
        answer=final_state["answer"],
        sources=sources,
        rag_context=rag_context,
        chunks_used=len(sources),
        provider=final_state["provider"],
        audit=audit,
    )