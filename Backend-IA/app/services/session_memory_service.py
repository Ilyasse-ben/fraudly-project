import json
from typing import List, Dict

from app.core.config import settings
from app.core.logger import get_logger


logger = get_logger(__name__)


_client = None


def _get_client():
    global _client

    if not settings.SESSION_MEMORY_ENABLED:
        return None

    if _client is not None:
        return _client

    try:
        import redis

        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return _client
    except Exception as e:
        logger.warning("[SessionMemory] Redis indisponible: %s", e)
        return None


def _key(session_id: str) -> str:
    return f"tutor:session:{session_id}:history"


def get_recent_turns(session_id: str) -> List[Dict[str, str]]:
    client = _get_client()
    if not client:
        return []

    try:
        key = _key(session_id)
        raw_items = client.lrange(key, 0, max(0, settings.SESSION_MEMORY_MAX_TURNS - 1))
        turns: List[Dict[str, str]] = []
        for raw in raw_items:
            item = json.loads(raw)
            user = str(item.get("user", "")).strip()
            assistant = str(item.get("assistant", "")).strip()
            if user or assistant:
                turns.append({"user": user, "assistant": assistant})
        return turns
    except Exception as e:
        logger.warning("[SessionMemory] Lecture impossible session=%s: %s", session_id, e)
        return []


def append_turn(session_id: str, user_question: str, assistant_answer: str) -> None:
    client = _get_client()
    if not client:
        return

    try:
        key = _key(session_id)
        payload = json.dumps(
            {
                "user": user_question,
                "assistant": assistant_answer,
            },
            ensure_ascii=False,
        )
        pipe = client.pipeline()
        pipe.lpush(key, payload)
        pipe.ltrim(key, 0, max(0, settings.SESSION_MEMORY_MAX_TURNS - 1))
        pipe.expire(key, settings.SESSION_MEMORY_TTL_SECONDS)
        pipe.execute()
    except Exception as e:
        logger.warning("[SessionMemory] Ecriture impossible session=%s: %s", session_id, e)


def build_session_context(turns: List[Dict[str, str]]) -> str:
    if not turns:
        return ""

    lines: List[str] = ["Contexte de conversation recent:"]
    for index, turn in enumerate(reversed(turns), 1):
        user = turn.get("user", "")
        assistant = turn.get("assistant", "")
        if user:
            lines.append(f"{index}. Etudiant: {user}")
        if assistant:
            lines.append(f"{index}. Tuteur: {assistant}")
    return "\n".join(lines)
