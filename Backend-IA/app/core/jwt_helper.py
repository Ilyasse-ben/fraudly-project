import base64
import time
import jwt
from app.core.config import settings


def generate_internal_token() -> str:
    """Génère un token ROLE_INTERNAL — même logique que InternalAuthMiddleware."""
    secret = settings.JWT_SECRET or ""
    try:
        key = base64.b64decode(secret, validate=True)
    except Exception:
        key = secret.encode()

    now = int(time.time())
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "userId": "00000000-0000-0000-0000-000000000001",
        "role": "ROLE_INTERNAL",
        "iat": now,
        "exp": now + 900
    }
    return jwt.encode(payload, key, algorithm="HS256")