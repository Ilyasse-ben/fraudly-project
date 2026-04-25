"""
LLM Router - invocation centralisee avec fallback configurable via .env.

Providers supportes:
- groq
- gemini
"""

from dataclasses import dataclass
import importlib
from typing import Optional

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

_SUPPORTED_PROVIDERS = {"groq", "gemini"}


@dataclass
class LLMCallResult:
    answer: Optional[str]
    provider: str
    fallback_used: bool
    error: Optional[str] = None


def _to_text(content: object) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    return str(content)


def _normalize_provider(value: str) -> str:
    return (value or "").strip().lower()


def _invoke_provider(provider: str, prompt: str) -> str:
    if provider == "groq":
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY manquante")

        ChatGroq = getattr(importlib.import_module("langchain_groq"), "ChatGroq")

        llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
        return _to_text(llm.invoke(prompt).content)

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY manquante")

        ChatGoogleGenerativeAI = getattr(
            importlib.import_module("langchain_google_genai"),
            "ChatGoogleGenerativeAI",
        )

        llm = ChatGoogleGenerativeAI(
            google_api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_output_tokens=settings.LLM_MAX_TOKENS,
        )
        return _to_text(llm.invoke(prompt).content)

    raise ValueError(f"Provider non supporte: {provider}")


def invoke_with_fallback(prompt: str) -> LLMCallResult:
    """
    Invoque le LLM en suivant l'ordre de fallback configure:
    1) settings.LLM_PROVIDER
    2) settings.LLM_FALLBACK_PROVIDER
    """
    primary = _normalize_provider(settings.LLM_PROVIDER)
    fallback = _normalize_provider(settings.LLM_FALLBACK_PROVIDER)

    provider_order = []
    for provider in (primary, fallback):
        if provider and provider not in provider_order:
            provider_order.append(provider)

    if not provider_order:
        return LLMCallResult(
            answer=None,
            provider="none",
            fallback_used=False,
            error="Aucun provider LLM configure (LLM_PROVIDER/LLM_FALLBACK_PROVIDER)",
        )

    errors = []
    for index, provider in enumerate(provider_order):
        if provider not in _SUPPORTED_PROVIDERS:
            msg = f"Provider inconnu dans config: {provider}"
            logger.warning(f"[LLMRouter] {msg}")
            errors.append(msg)
            continue

        try:
            answer = _invoke_provider(provider, prompt)
            logger.info(
                "[LLMRouter] Reponse generee provider=%s fallback_used=%s",
                provider,
                index > 0,
            )
            return LLMCallResult(
                answer=answer,
                provider=provider,
                fallback_used=index > 0,
                error=None,
            )
        except Exception as e:
            msg = f"{provider} failed: {e}"
            logger.warning(f"[LLMRouter] {msg}")
            errors.append(msg)

    return LLMCallResult(
        answer=None,
        provider="none",
        fallback_used=False,
        error="; ".join(errors) if errors else "Tous les providers ont echoue",
    )
