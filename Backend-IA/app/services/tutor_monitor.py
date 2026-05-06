from typing import Any, Dict, List

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings
from app.core.logger import get_logger
from app.services.embedding_service import embed_chunks
from app.services.session_memory_service import get_recent_turns

logger = get_logger(__name__)


def _sanitize_question(value: Any) -> str:
    return str(value or "").strip()


def detect_student_block(session_id: str) -> Dict[str, Any]:
    """
    Detect if a student appears blocked in tutor session based on semantic repetition.

    Returns a dict with:
    - blocked: bool
    - reason: str | None
    - details: dict
    """
    similarity_threshold = settings.TUTOR_BLOCK_SIMILARITY_THRESHOLD
    min_turns = settings.TUTOR_BLOCK_MIN_TURNS
    lookback_window = settings.TUTOR_BLOCK_LOOKBACK_WINDOW
    high_sim_count_threshold = settings.TUTOR_BLOCK_HIGH_SIM_COUNT_THRESHOLD

    turns = get_recent_turns(session_id)
    if len(turns) < min_turns:
        return {"blocked": False, "reason": None, "details": {}}

    questions: List[str] = []
    for turn in turns:
        q = _sanitize_question(turn.get("user"))
        if q:
            questions.append(q)

    if len(questions) < min_turns:
        return {"blocked": False, "reason": None, "details": {}}

    # Session memory stores newest first (LPUSH), so reverse to chronological order.
    ordered_questions = list(reversed(questions))
    current_question = ordered_questions[-1]
    previous_questions = ordered_questions[-(lookback_window + 1) : -1]

    if not previous_questions:
        return {"blocked": False, "reason": None, "details": {}}

    texts = previous_questions + [current_question]

    try:
        vectors = np.asarray(embed_chunks(texts), dtype=np.float32)
        if vectors.ndim != 2 or vectors.shape[0] != len(texts):
            logger.warning("[TutorMonitor] Invalid embedding shape session=%s", session_id)
            return {"blocked": False, "reason": None, "details": {}}

        current_vec = vectors[-1].reshape(1, -1)
        prev_vecs = vectors[:-1]
        similarities = cosine_similarity(current_vec, prev_vecs)[0]

        avg_similarity = float(np.mean(similarities))
        high_similarity_count = int(np.sum(similarities >= similarity_threshold))

        if high_similarity_count >= high_sim_count_threshold:
            return {
                "blocked": True,
                "reason": "high_repetition",
                "details": {
                    "avg_similarity": round(avg_similarity, 4),
                    "high_similarity_count": high_similarity_count,
                    "threshold": similarity_threshold,
                    "lookback": len(previous_questions),
                    "question_preview": current_question[:120],
                },
            }

        if avg_similarity >= similarity_threshold:
            return {
                "blocked": True,
                "reason": "stuck_on_topic",
                "details": {
                    "avg_similarity": round(avg_similarity, 4),
                    "high_similarity_count": high_similarity_count,
                    "threshold": similarity_threshold,
                    "lookback": len(previous_questions),
                    "question_preview": current_question[:120],
                },
            }

        return {
            "blocked": False,
            "reason": None,
            "details": {
                "avg_similarity": round(avg_similarity, 4),
                "high_similarity_count": high_similarity_count,
            },
        }
    except Exception as e:
        logger.error("[TutorMonitor] Detection error session=%s: %s", session_id, e)
        return {"blocked": False, "reason": None, "details": {}}
