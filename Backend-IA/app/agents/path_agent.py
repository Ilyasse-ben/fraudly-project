"""
Learning Path Engine - recommandations de parcours personalisees.

Le moteur utilise uniquement l'historique d'apprentissage disponible dans le profil
et priorise les chapitres en fonction des lacunes, des scores faibles et du niveau
de maitrise global.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Tuple

from app.core.logger import get_logger
from app.schemas.path_schema import LearningPathResponse, RecommendedStep, StudentProfile


logger = get_logger(__name__)

LOW_SCORE_THRESHOLD = 0.60
CONSOLIDATION_THRESHOLD = 0.80
MAX_RECOMMENDED_STEPS = 5


def _coerce_score(value: object) -> Optional[float]:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, score))


def _unique(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    ordered: List[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _priority_label(score: Optional[float], completed: bool, weak_topic: bool) -> Tuple[int, str]:
    if weak_topic or (score is not None and score < LOW_SCORE_THRESHOLD):
        return 1, "urgence"
    if score is not None and score < CONSOLIDATION_THRESHOLD:
        return 2, "consolidation"
    if not completed:
        return 2, "progression"
    return 3, "approfondissement"


def _build_reason(chapter_id: str, score: Optional[float], completed: bool, weak_topic: bool) -> str:
    parts: List[str] = []
    if weak_topic:
        parts.append("faiblesse signalee dans l'historique")
    if score is not None:
        parts.append(f"score actuel {score:.0%}")
    if completed:
        parts.append("deja traite")
    else:
        parts.append("pas encore termine")
    if not parts:
        parts.append("aucun signal disponible")
    return f"{chapter_id}: " + ", ".join(parts)


def _build_candidates(profile: StudentProfile) -> List[Tuple[str, Optional[float], bool, bool]]:
    scores = {chapter_id: _coerce_score(score) for chapter_id, score in profile.scores.items()}
    completed = set(profile.completed_chapters)
    weak_topics = set(profile.weak_topics)

    identifiers = _unique([
        *profile.weak_topics,
        *profile.completed_chapters,
        *scores.keys(),
    ])

    candidates: List[Tuple[str, Optional[float], bool, bool]] = []
    for chapter_id in identifiers:
        score = scores.get(chapter_id)
        is_completed = chapter_id in completed
        is_weak = chapter_id in weak_topics

        if score is None and not is_weak and not is_completed:
            continue

        candidates.append((chapter_id, score, is_completed, is_weak))

    return candidates


def recommend_learning_path(profile: StudentProfile) -> LearningPathResponse:
    """Construit un parcours personnalise a partir de l'historique et des lacunes."""

    validated_profile = StudentProfile.model_validate(profile)
    candidates = _build_candidates(validated_profile)

    if not candidates:
        fallback_step = RecommendedStep(
            chapter_id=validated_profile.completed_chapters[-1] if validated_profile.completed_chapters else "onboarding",
            reason="Aucun signal d'historique exploitable; proposer une reprise generale.",
            priority=2,
        )
        summary = (
            "Parcours de reprise generalise: aucune lacune explicite detectee, "
            "le plan demarre par une consolidation large."
        )
        logger.info(
            "[PathAgent] student=%s course=%s -> fallback path",
            validated_profile.student_id,
            validated_profile.course_id,
        )
        return LearningPathResponse(
            student_id=validated_profile.student_id,
            course_id=validated_profile.course_id,
            recommended_steps=[fallback_step],
            summary=summary,
            provider="heuristic",
        )

    ranked = sorted(
        candidates,
        key=lambda item: (
            _priority_label(item[1], item[2], item[3])[0],
            1.0 if item[1] is None else item[1],
            item[0],
        ),
    )

    steps: List[RecommendedStep] = []
    for chapter_id, score, completed, weak_topic in ranked:
        priority, _ = _priority_label(score, completed, weak_topic)
        steps.append(
            RecommendedStep(
                chapter_id=chapter_id,
                reason=_build_reason(chapter_id, score, completed, weak_topic),
                priority=priority,
            )
        )
        if len(steps) >= MAX_RECOMMENDED_STEPS:
            break

    gap_count = sum(step.priority == 1 for step in steps)
    consolidation_count = sum(step.priority == 2 for step in steps)
    mastery_count = sum(step.priority == 3 for step in steps)

    if gap_count:
        summary = (
            f"Parcours centre sur {gap_count} lacune(s) prioritaire(s) et "
            f"{consolidation_count} chapitre(s) a consolider."
        )
    elif consolidation_count:
        summary = (
            f"Parcours de consolidation avec {consolidation_count} chapitre(s) a renforcer "
            f"et {mastery_count} suggestion(s) d'approfondissement."
        )
    else:
        summary = (
            f"Parcours d'approfondissement: {mastery_count} chapitre(s) deja maitris(es) "
            "sont proposes pour aller plus loin."
        )

    logger.info(
        "[PathAgent] student=%s course=%s completed=%d weak=%d scores=%d steps=%d",
        validated_profile.student_id,
        validated_profile.course_id,
        len(validated_profile.completed_chapters),
        len(validated_profile.weak_topics),
        len(validated_profile.scores),
        len(steps),
    )

    return LearningPathResponse(
        student_id=validated_profile.student_id,
        course_id=validated_profile.course_id,
        recommended_steps=steps,
        summary=summary,
        provider="heuristic",
    )