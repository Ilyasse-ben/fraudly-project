"""
RAG Quality Evaluation — Métriques de qualité du pipeline RAG.
Implémente RAGAS (Retrieval-Augmented Generation Assessment) et dérivés.

Métriques principales :
- Faithfulness: Le résultat LLM reste-t-il fidèle au contexte fourni?
- Relevancy: Les chunks retournés sont-ils pertinents à la question?
- Answer Relevancy: La réponse LLM répond-elle à la question?
- Context Precision: Quel % du contexte est pertinent?
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RAGMetrics:
    """Résultat d'évaluation RAG."""
    faithfulness: float  # 0-1: Fidélité réponse au contexte
    relevancy: float     # 0-1: Pertinence chunks au query
    answer_relevancy: float  # 0-1: La réponse répond à la question
    context_precision: float  # 0-1: % du contexte pertinent
    overall_score: float  # 0-1: Score agrégé
    
    def to_dict(self) -> Dict:
        return {
            "faithfulness": round(self.faithfulness, 4),
            "relevancy": round(self.relevancy, 4),
            "answer_relevancy": round(self.answer_relevancy, 4),
            "context_precision": round(self.context_precision, 4),
            "overall_score": round(self.overall_score, 4),
        }


def _simple_overlap_score(text1: str, text2: str) -> float:
    """
    Score de chevauchement simple basé sur les mots communs.
    Heuristique fast pour approx de similarité.
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


def evaluate_faithfulness(
    context: str,
    llm_response: str,
    threshold: float = 0.3,
) -> float:
    """
    Faithfulness: Mesure si la réponse LLM reste fidèle au contexte.
    
    Implémentation rapide: compte les déclarations de la réponse qui sont
    soutenues par le contexte (via chevauchement lexical).
    
    Approche complète (non implémentée ici): extrait les claims de la réponse
    et vérifie chacun contre le contexte avec un NLI model.
    
    Args:
        context: Contexte fourni (chunks)
        llm_response: Réponse générée par le LLM
        threshold: Seuil de chevauchement minimum
    
    Returns:
        Score 0-1 : faithfulness
    """
    if not context or not llm_response:
        return 0.0
    
    # Approche simple : calculer le chevauchement global
    # En production : utiliser un modèle NLI ou un LLM pour fact-checking
    overlap = _simple_overlap_score(context, llm_response)
    
    # Mapper overlap à faithfulness (overlap >= threshold → score élevé)
    faithfulness = max(0.0, min(1.0, overlap / threshold)) if threshold > 0 else overlap
    
    logger.debug(f"[RAGAS] Faithfulness: {faithfulness:.4f} (overlap={overlap:.4f})")
    return faithfulness


def evaluate_relevancy(
    query: str,
    retrieved_contexts: List[str],
    scores: Optional[List[float]] = None,
) -> float:
    """
    Relevancy: Mesure si les chunks retournés sont pertinents à la question.
    
    Utilise les scores de similarité fournis par le modèle d'embedding
    ou calcule un chevauchement lexical simple.
    
    Args:
        query: Question utilisateur
        retrieved_contexts: Liste des chunks retournés
        scores: Scores de similarité (optionnel, 0-1)
    
    Returns:
        Score 0-1 : relevancy moyen
    """
    if not retrieved_contexts:
        return 0.0
    
    if scores:
        # Utiliser les scores d'embedding s'ils sont disponibles
        avg_score = sum(scores) / len(scores)
        relevancy = avg_score
    else:
        # Calculer le chevauchement lexical
        overlaps = [_simple_overlap_score(query, ctx) for ctx in retrieved_contexts]
        relevancy = sum(overlaps) / len(overlaps) if overlaps else 0.0
    
    relevancy = max(0.0, min(1.0, relevancy))
    logger.debug(f"[RAGAS] Relevancy: {relevancy:.4f}")
    return relevancy


def evaluate_answer_relevancy(
    query: str,
    llm_response: str,
) -> float:
    """
    Answer Relevancy: Mesure si la réponse répond réellement à la question.
    
    Implémentation rapide: chevauchement entre la question et la réponse.
    En production: utiliser un modèle NLI ou un LLM "judge" externe.
    
    Args:
        query: Question originale
        llm_response: Réponse générée
    
    Returns:
        Score 0-1 : answer_relevancy
    """
    if not query or not llm_response:
        return 0.0
    
    # Chevauchement lexical simple
    overlap = _simple_overlap_score(query, llm_response)
    
    # Heuristique: si > 50% des mots de la question sont dans la réponse,
    # c'est un bon signe qu'elle répond à la question
    answer_relevancy = min(1.0, overlap * 2.0)  # Amplifier le score
    
    logger.debug(f"[RAGAS] Answer Relevancy: {answer_relevancy:.4f}")
    return answer_relevancy


def evaluate_context_precision(
    query: str,
    retrieved_contexts: List[str],
    scores: Optional[List[float]] = None,
    threshold: float = 0.3,
) -> float:
    """
    Context Precision: Quel pourcentage du contexte retourné est pertinent?
    
    Approche rapide: compte les chunks avec un chevauchement > threshold
    avec la question.
    
    Args:
        query: Question utilisateur
        retrieved_contexts: Liste des chunks retournés
        scores: Scores de similarité (optionnel)
        threshold: Seuil de pertinence minimum
    
    Returns:
        Score 0-1 : pourcentage de contexte pertinent
    """
    if not retrieved_contexts:
        return 0.0
    
    if scores:
        # Utiliser les scores d'embedding
        relevant_count = sum(1 for s in scores if s >= threshold)
    else:
        # Utiliser le chevauchement lexical
        relevant_count = sum(
            1 for ctx in retrieved_contexts
            if _simple_overlap_score(query, ctx) >= threshold
        )
    
    context_precision = relevant_count / len(retrieved_contexts)
    logger.debug(f"[RAGAS] Context Precision: {context_precision:.4f}")
    return context_precision


def evaluate_rag(
    query: str,
    retrieved_contexts: List[str],
    llm_response: str,
    scores: Optional[List[float]] = None,
) -> RAGMetrics:
    """
    Évaluation complète du pipeline RAG.
    
    Calcule les 4 métriques RAGAS et un score global.
    
    Args:
        query: Question utilisateur
        retrieved_contexts: Chunks retournés par la recherche
        llm_response: Réponse générée par le LLM
        scores: Scores de similarité optionnels (0-1)
    
    Returns:
        RAGMetrics avec tous les scores
    """
    context_str = "\n\n".join(retrieved_contexts)
    
    faithfulness = evaluate_faithfulness(context_str, llm_response)
    relevancy = evaluate_relevancy(query, retrieved_contexts, scores)
    answer_relevancy = evaluate_answer_relevancy(query, llm_response)
    context_precision = evaluate_context_precision(query, retrieved_contexts, scores)
    
    # Score global = moyenne pondérée
    overall_score = (
        faithfulness * 0.3 +
        relevancy * 0.3 +
        answer_relevancy * 0.2 +
        context_precision * 0.2
    )
    
    metrics = RAGMetrics(
        faithfulness=faithfulness,
        relevancy=relevancy,
        answer_relevancy=answer_relevancy,
        context_precision=context_precision,
        overall_score=overall_score,
    )
    
    logger.info(f"[RAGAS] Évaluation complète: {json.dumps(metrics.to_dict())}")
    return metrics


def batch_evaluate_rag(
    test_cases: List[Dict],
) -> List[RAGMetrics]:
    """
    Évalue un batch de test cases RAG.
    
    Args:
        test_cases: Liste de dicts {query, contexts, response, scores?}
    
    Returns:
        Liste de RAGMetrics
    """
    results = []
    for i, case in enumerate(test_cases):
        logger.info(f"[RAGAS] Évaluant cas {i+1}/{len(test_cases)}")
        
        metrics = evaluate_rag(
            query=case["query"],
            retrieved_contexts=case["contexts"],
            llm_response=case["response"],
            scores=case.get("scores"),
        )
        results.append(metrics)
    
    # Statistiques agrégées
    if results:
        avg_faith = sum(m.faithfulness for m in results) / len(results)
        avg_relev = sum(m.relevancy for m in results) / len(results)
        avg_ans_relev = sum(m.answer_relevancy for m in results) / len(results)
        avg_ctx_prec = sum(m.context_precision for m in results) / len(results)
        avg_overall = sum(m.overall_score for m in results) / len(results)
        
        logger.info(
            f"[RAGAS] Résumé {len(results)} cas — "
            f"Faith={avg_faith:.4f} Relev={avg_relev:.4f} "
            f"AnsRelev={avg_ans_relev:.4f} CtxPrec={avg_ctx_prec:.4f} "
            f"Overall={avg_overall:.4f}"
        )
    
    return results
