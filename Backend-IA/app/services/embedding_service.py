"""
Embedding Service — encodage texte → vecteurs via SentenceTransformer.

IMPORTANT sur les préfixes "query:" / "passage:" :
    Ces préfixes sont une exigence du modèle intfloat/multilingual-e5-*.
    Si EMBEDDING_MODEL est modifié dans .env pour un autre modèle,
    ces préfixes doivent être vérifiés / supprimés pour éviter une
    dégradation silencieuse de la qualité du retrieval.
"""

from sentence_transformers import SentenceTransformer
from typing import List, Optional
import torch
import time
import numpy as np

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

_model: Optional[SentenceTransformer] = None

# Modèles E5 qui nécessitent les préfixes "query:" / "passage:".
# Tout autre modèle ne doit PAS recevoir ces préfixes.
_E5_MODEL_PREFIXES = ("intfloat/multilingual-e5", "intfloat/e5")


def _requires_e5_prefix() -> bool:
    """Vérifie si le modèle configuré est un modèle E5 nécessitant les préfixes."""
    return settings.EMBEDDING_MODEL.startswith(_E5_MODEL_PREFIXES)


# ─────────────────────────────
# MODEL SINGLETON
# ─────────────────────────────
def get_embedding_model() -> SentenceTransformer:
    global _model

    if _model is None:
        device = settings.EMBEDDING_DEVICE

        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("[Embedding] CUDA demandé mais indisponible → fallback CPU")
            device = "cpu"

        logger.info(f"[Embedding] Chargement {settings.EMBEDDING_MODEL} sur {device}")

        if not _requires_e5_prefix():
            logger.warning(
                f"[Embedding] Le modèle '{settings.EMBEDDING_MODEL}' n'est pas un modèle E5. "
                "Les préfixes 'query:' / 'passage:' ne seront PAS appliqués. "
                "Vérifiez que cela correspond au comportement attendu."
            )

        start  = time.time()
        _model = SentenceTransformer(settings.EMBEDDING_MODEL, device=device)

        logger.info(f"[Embedding] Modèle prêt en {time.time() - start:.2f}s")

    return _model


# ─────────────────────────────
# SAFE CHUNK EMBEDDING
# ─────────────────────────────
def embed_chunks(texts: List[str]) -> List[List[float]]:
    """
    Encode une liste de chunks (passages) en vecteurs normalisés.
    Utilise le préfixe "passage:" pour les modèles E5.
    """
    if not texts:
        return []

    model      = get_embedding_model()
    use_prefix = _requires_e5_prefix()

    logger.info(f"[Embedding] Encodage {len(texts)} chunks (préfixe E5: {use_prefix})")

    try:
        inputs = [f"passage: {t}" for t in texts] if use_prefix else texts

        embeddings = model.encode(
            inputs,
            normalize_embeddings=True,
            batch_size=16,
            show_progress_bar=False,
        )

        embeddings = np.asarray(embeddings, dtype=np.float32)

        if len(embeddings) != len(texts):
            raise ValueError(
                f"Mismatch embeddings/textes : {len(embeddings)} vecteurs pour {len(texts)} textes"
            )

        return embeddings.tolist()

    except Exception as e:
        logger.exception(f"[Embedding] ERREUR encodage chunks: {e}")
        raise


# ─────────────────────────────
# SAFE QUERY EMBEDDING
# ─────────────────────────────
def embed_query(query: str) -> List[float]:
    """
    Encode une requête utilisateur en vecteur normalisé.
    FIX : lève ValueError sur chaîne vide au lieu de retourner [] silencieusement.
    Un vecteur vide transmis à ChromaDB provoque une exception obscure difficile à déboguer.
    Utilise le préfixe "query:" pour les modèles E5.
    """
    if not query or not query.strip():
        raise ValueError("[Embedding] embed_query() appelé avec une requête vide.")

    model      = get_embedding_model()
    use_prefix = _requires_e5_prefix()

    try:
        input_text = f"query: {query}" if use_prefix else query

        emb = model.encode(
            input_text,
            normalize_embeddings=True,
        )

        return np.asarray(emb, dtype=np.float32).tolist()

    except Exception as e:
        logger.exception(f"[Embedding] ERREUR encodage requête: {e}")
        raise


def warm_up_model() -> SentenceTransformer:
    """
    Compatibilité ascendante: précharge le modèle d'embedding.
    Conservé pour les scripts manuels (ex: test_rag.py).
    """
    return get_embedding_model()