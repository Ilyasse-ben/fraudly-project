"""
Assessment Agent – génération d'évaluations (QCM / Vrai-Faux / Ouvertes)
avec contexte RAG et configuration professeur.
"""

import json
import math
from typing import List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from app.core.logger import get_logger
from app.schemas.assessment_schema import (
	AssessmentAuditTrail,
	AssessmentGenerateRequest,
	AssessmentGenerateResponse,
	AssessmentQuestion,
	ContextChunk,
	SourceChunk,
)
from app.schemas.rag_schema import KnowledgeChunk
from app.services.llm_router import invoke_with_fallback
from app.services.rag_service import search

logger = get_logger(__name__)


class AssessmentState(TypedDict):
	topic: str
	course_id: Optional[str]
	chapter_id: Optional[str]
	chapter_ids: Optional[List[str]]
	top_k: int
	difficulty: str
	total_questions: int
	qcm_count: int
	true_false_count: int
	open_count: int
	include_explanations: bool
	professor_instructions: Optional[str]
	chunks: List[KnowledgeChunk]
	prompt: str
	answer: str
	parsed_questions: List[AssessmentQuestion]
	provider: str
	fallback_used: bool
	error: Optional[str]


def _resolve_distribution(total: int, qcm: int, tf: int, open_q: int) -> tuple[int, int, int]:
	specified = qcm + tf + open_q
	if specified > 0:
		if specified != total:
			raise ValueError(
				"La somme qcm_count + true_false_count + open_count doit égale à total_questions."
			)
		return qcm, tf, open_q

	# Répartition par défaut
	auto_qcm = max(1, math.floor(total * 0.4))
	auto_tf = max(1, math.floor(total * 0.3))
	auto_open = total - auto_qcm - auto_tf
	if auto_open < 1:
		auto_open = 1
		auto_tf = max(1, total - auto_qcm - auto_open)
	auto_qcm = total - auto_tf - auto_open
	return auto_qcm, auto_tf, auto_open


def _format_context(chunks: List[KnowledgeChunk]) -> str:
	if not chunks:
		return "Aucun contenu pertinent trouvé dans la base de connaissances."

	entries = []
	for i, c in enumerate(chunks, 1):
		entries.append(
			f"[Source {i}] {c.source_file} (page {c.page}) | score {c.score}\n{c.content}"
		)
	return "\n\n".join(entries)


def _build_assessment_prompt(state: AssessmentState) -> str:
	explain_rule = (
		"Ajoute une explication courte par question."
		if state["include_explanations"]
		else "N'ajoute pas de champ explanation"
	)

	prof_instructions = state.get("professor_instructions") or "Aucune instruction additionnelle."
	chapter_line = ""
	if state.get("chapter_ids"):
		chapter_line = f"- Chapitres ciblés: {', '.join(state['chapter_ids'])}\n"
	elif state.get("chapter_id"):
		chapter_line = f"- Chapitre ciblé: {state['chapter_id']}\n"

	return (
		"Tu es un expert pédagogique chargé de construire une évaluation.\n"
		"Tu dois STRICTEMENT utiliser le contexte fourni, sans inventer.\n\n"
		"CONTRAINTES:\n"
		f"- Difficulté globale: {state['difficulty']}\n"
		f"- Nombre total de questions: {state['total_questions']}\n"
		f"- Nombre QCM: {state['qcm_count']}\n"
		f"- Nombre Vrai/Faux: {state['true_false_count']}\n"
		f"- Nombre Questions ouvertes: {state['open_count']}\n"
		"- Les questions doivent couvrir des idées différentes du contenu\n"
		"- Mélanger rappel, compréhension et application selon la difficulté\n"
		f"- {explain_rule}\n"
		"- Chaque question doit inclure max_score (points de la question, > 0)\n"
		"- Pour les QCM: 4 choix (A/B/C/D), un seul correct\n"
		"- Pour Vrai/Faux: correct_answer doit être 'Vrai' ou 'Faux'\n"
		"- Pour ouverte: correct_answer attendu = réponse modèle concise\n\n"
		"INSTRUCTIONS PROFESSEUR:\n"
		f"{prof_instructions}\n\n"
		"SUJET:\n"
		f"{state['topic']}\n\n"
		"PÉRIMÈTRE PÉDAGOGIQUE:\n"
		f"{chapter_line}"
		"\n"
		"CONTEXTE:\n"
		f"{_format_context(state['chunks'])}\n\n"
		"FORMAT DE SORTIE OBLIGATOIRE:\n"
		"Retourne UNIQUEMENT un JSON valide (sans markdown) au format:\n"
		"{\n"
		"  \"questions\": [\n"
		"    {\n"
		"      \"id\": 1,\n"
		"      \"type\": \"qcm|vrai_faux|ouverte\",\n"
		"      \"difficulty\": \"facile|moyen|difficile\",\n"
		"      \"question\": \"...\",\n"
		"      \"choices\": [\n"
		"        {\"label\": \"A\", \"text\": \"...\", \"is_correct\": false}\n"
		"      ],\n"
		"      \"correct_answer\": \"...\",\n"
		"      \"max_score\": 1,\n"
		"      \"explanation\": \"...\"\n"
		"    }\n"
		"  ]\n"
		"}\n"
	)


def _strip_json_fence(text: str) -> str:
	raw = text.strip()
	if raw.startswith("```"):
		lines = raw.splitlines()
		if lines and lines[0].startswith("```"):
			lines = lines[1:]
		if lines and lines[-1].strip() == "```":
			lines = lines[:-1]
		raw = "\n".join(lines).strip()
		if raw.lower().startswith("json"):
			raw = raw[4:].strip()
	return raw


def _parse_questions(raw_answer: str) -> List[AssessmentQuestion]:
	clean = _strip_json_fence(raw_answer)
	payload = json.loads(clean)
	items = payload.get("questions", [])
	if not isinstance(items, list):
		raise ValueError("Le JSON généré ne contient pas une liste 'questions' valide.")
	return [AssessmentQuestion.model_validate(item) for item in items]


def retrieve_node(state: AssessmentState) -> AssessmentState:
	logger.info(f"[AssessmentAgent] RETRIEVE → '{state['topic'][:60]}'")
	result = search(
		query=state["topic"],
		course_id=state.get("course_id"),
		chapter_id=state.get("chapter_id"),
		chapter_ids=state.get("chapter_ids"),
		top_k=state["top_k"],
	)
	return {**state, "chunks": result.chunks}


def generate_node(state: AssessmentState) -> AssessmentState:
	prompt = _build_assessment_prompt(state)

	llm_result = invoke_with_fallback(prompt)
	if llm_result.answer:
		return {
			**state,
			"prompt": prompt,
			"answer": llm_result.answer,
			"provider": llm_result.provider,
			"fallback_used": llm_result.fallback_used,
		}

	return {
		**state,
		"prompt": prompt,
		"answer": "",
		"provider": "none",
		"fallback_used": False,
		"error": llm_result.error or "Aucun LLM configuré ou tous les LLM ont échoué à générer une réponse.",
	}


def parse_node(state: AssessmentState) -> AssessmentState:
	if state.get("error"):
		return state

	try:
		parsed = _parse_questions(state["answer"])
		return {**state, "parsed_questions": parsed}
	except Exception as e:
		logger.error(f"[AssessmentAgent] Parsing JSON failed: {e}")
		return {
			**state,
			"parsed_questions": [],
			"error": f"Réponse LLM invalide (JSON non conforme): {e}",
		}


def build_assessment_graph() -> StateGraph:
	graph = StateGraph(AssessmentState)
	graph.add_node("retrieve", retrieve_node)
	graph.add_node("generate", generate_node)
	graph.add_node("parse", parse_node)
	graph.set_entry_point("retrieve")
	graph.add_edge("retrieve", "generate")
	graph.add_edge("generate", "parse")
	graph.add_edge("parse", END)
	return graph.compile()


_assessment_graph = None


def get_assessment_graph():
	global _assessment_graph
	if _assessment_graph is None:
		_assessment_graph = build_assessment_graph()
	return _assessment_graph


def generate_assessment(request: AssessmentGenerateRequest) -> AssessmentGenerateResponse:
	qcm_count, tf_count, open_count = _resolve_distribution(
		request.total_questions,
		request.qcm_count,
		request.true_false_count,
		request.open_count,
	)

	initial_state: AssessmentState = {
		"topic": request.topic,
		"course_id": request.course_id,
		"chapter_id": request.chapter_id,
		"chapter_ids": request.chapter_ids,
		"top_k": request.top_k,
		"difficulty": request.difficulty,
		"total_questions": request.total_questions,
		"qcm_count": qcm_count,
		"true_false_count": tf_count,
		"open_count": open_count,
		"include_explanations": request.include_explanations,
		"professor_instructions": request.professor_instructions,
		"chunks": [],
		"prompt": "",
		"answer": "",
		"parsed_questions": [],
		"provider": "none",
		"fallback_used": False,
		"error": None,
	}

	graph = get_assessment_graph()
	final_state = graph.invoke(initial_state)

	if final_state.get("error"):
		raise ValueError(final_state["error"])

	questions = final_state["parsed_questions"]
	if len(questions) != request.total_questions:
		raise ValueError(
			f"Le LLM a généré {len(questions)} questions au lieu de {request.total_questions}."
		)

	sources = [
		SourceChunk(source_file=c.source_file, page=c.page, score=c.score)
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

	distribution = {
		"qcm": len([q for q in questions if q.type == "qcm"]),
		"vrai_faux": len([q for q in questions if q.type == "vrai_faux"]),
		"ouverte": len([q for q in questions if q.type == "ouverte"]),
	}

	audit = AssessmentAuditTrail(
		provider=final_state["provider"],
		fallback_used=final_state["fallback_used"],
		retrieved_chunks=len(final_state["chunks"]),
		prompt_chars=len(final_state["prompt"]),
		generated_questions=len(questions),
		requested_difficulty=request.difficulty,
	)

	logger.info(
		"[AssessmentAgent][AUDIT] "
		f"provider={audit.provider} fallback={audit.fallback_used} "
		f"difficulty={request.difficulty} generated={audit.generated_questions} "
		f"topic='{request.topic[:80]}'"
	)

	return AssessmentGenerateResponse(
		topic=request.topic,
		difficulty=request.difficulty,
		total_requested=request.total_questions,
		total_generated=len(questions),
		distribution=distribution,
		questions=questions,
		sources=sources,
		rag_context=rag_context,
		provider=final_state["provider"],
		audit=audit,
	)
