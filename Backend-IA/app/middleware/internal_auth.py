import base64
import binascii
import jwt
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

EXCLUDED_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


class InternalAuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        if request.url.path in EXCLUDED_PATHS:  # ✅ maintenant défini
            return await call_next(request)

        auth = request.headers.get("Authorization")

        if not auth or not auth.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing token"})

        token = auth.split(" ", 1)[1]

        secret = settings.JWT_SECRET or ""
        try:
            key = base64.b64decode(secret, validate=True)
        except binascii.Error:
            key = secret.encode()

        try:
            payload = jwt.decode(token, key, algorithms=["HS256"])
            if payload.get("role") != "ROLE_INTERNAL":
                return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        except jwt.ExpiredSignatureError:
            return JSONResponse(status_code=401, content={"detail": "Token expired"})
        except Exception:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        return await call_next(request)