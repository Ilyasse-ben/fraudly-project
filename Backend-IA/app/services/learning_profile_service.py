import json
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from app.core.config import settings
from app.core.logger import get_logger


logger = get_logger(__name__)


def fetch_student_profile(student_id: str, course_id: Optional[str] = None) -> Dict[str, Any]:
    """Fetch aggregated student profile from Learning Service analytics API."""
    base = settings.ANALYTICS_SERVICE_BASE_URL.rstrip("/")
    endpoint = f"{base}/students/{student_id}/profile"

    if course_id:
        endpoint = f"{endpoint}?{urlencode({'courseId': course_id})}"

    try:
        with urlopen(endpoint, timeout=settings.ANALYTICS_SERVICE_TIMEOUT_SECONDS) as response:
            payload = response.read().decode("utf-8")
            data = json.loads(payload)
            if not isinstance(data, dict):
                raise RuntimeError("Réponse profile invalide: objet attendu")
            return data
    except HTTPError as e:
        details = e.read().decode("utf-8", errors="ignore")
        logger.error("[LearningProfile] HTTP %s sur %s: %s", e.code, endpoint, details)
        raise RuntimeError(f"Learning Service HTTP {e.code}")
    except URLError as e:
        logger.error("[LearningProfile] Service indisponible %s: %s", endpoint, e)
        raise RuntimeError("Learning Service indisponible")
    except json.JSONDecodeError as e:
        logger.error("[LearningProfile] JSON invalide %s: %s", endpoint, e)
        raise RuntimeError("Learning Service a retourné un JSON invalide")
