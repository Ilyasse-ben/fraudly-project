"""
ChromaDB Client — gestion centralisée de la base vectorielle.

Responsabilités :
- Initialiser ChromaDB (persistant)
- Fournir un singleton de collection
- Gérer les utilitaires (stats, reset, persist)

Utilisé par :
- rag_service uniquement (ingestion + retrieval)
"""

import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import Optional, List
import math
import re
import json
from pathlib import Path

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

os.makedirs(settings.CHROMA_PATH, exist_ok=True)

_client: Optional[chromadb.ClientAPI] = None
_collection = None

# Taille de page pour la pagination de get_distinct_course_ids().
# FIX : l'appel col.get() sans limite chargeait TOUS les vecteurs en RAM,
# ce qui pouvait saturer la mémoire sur une collection de plusieurs millions de chunks.
_PAGINATION_BATCH = 1_000
_DIMENSION_MISMATCH_RE = re.compile(r"dimension of (\d+), got (\d+)", re.IGNORECASE)


class _SimplePersistentCollection:
    """Lightweight file-backed collection used as the default reliable backend."""

    def __init__(self, name: str):
        self.name = name
        self._store_path = Path(settings.CHROMA_PATH) / f"{name}.json"
        self._records: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not self._store_path.exists():
            return
        try:
            with self._store_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            records = payload.get("records", {})
            if isinstance(records, dict):
                self._records = records
        except Exception as e:
            logger.warning(f"[SimpleStore] Impossible de charger {self._store_path}: {e}")

    def _save(self) -> None:
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._store_path.with_suffix(".json.tmp")
        payload = {"name": self.name, "records": self._records}
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False)
        tmp_path.replace(self._store_path)

    def add(self, ids, embeddings, documents, metadatas):
        for item_id, embedding, document, metadata in zip(ids, embeddings, documents, metadatas):
            self._records[item_id] = {
                "embedding": embedding,
                "document": document,
                "metadata": metadata or {},
            }
        self._save()

    def count(self):
        return len(self._records)

    def get(self, include=None, limit=None, offset=0):
        items = list(self._records.values())
        sliced = items[offset : offset + (limit or len(items))]
        return {"metadatas": [item.get("metadata", {}) for item in sliced]}

    def query(self, query_embeddings, n_results=5, where=None, include=None):
        if not self._records:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        query_embedding = query_embeddings[0]

        def _match(metadata):
            if where is None:
                return True
            if "$and" in where:
                return all(metadata.get(list(f.keys())[0]) == list(f.values())[0] for f in where["$and"])
            key, value = list(where.items())[0]
            return metadata.get(key) == value

        def _cosine_distance(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(y * y for y in b))
            if norm_a == 0 or norm_b == 0:
                return 1.0
            return 1.0 - (dot / (norm_a * norm_b))

        candidates = []
        for record in self._records.values():
            metadata = record.get("metadata", {})
            if _match(metadata):
                candidates.append(record)

        if not candidates:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        scored = [
            (record, _cosine_distance(query_embedding, record["embedding"]))
            for record in candidates
        ]
        scored.sort(key=lambda item: item[1])
        top = scored[:n_results]

        return {
            "documents": [[record[0]["document"] for record in top]],
            "metadatas": [[record[0]["metadata"] for record in top]],
            "distances": [[distance for _, distance in top]],
        }


class _InMemoryCollection:
    """Fallback collection for environments where native Chroma crashes."""

    def __init__(self, name: str):
        self.name = name
        self._docs = {}
        self._metas = {}
        self._embeds = {}

    def add(self, ids, embeddings, documents, metadatas):
        for i, emb, doc, meta in zip(ids, embeddings, documents, metadatas):
            self._docs[i] = doc
            self._metas[i] = meta or {}
            self._embeds[i] = emb

    def count(self):
        return len(self._docs)

    def get(self, include=None, limit=None, offset=0):
        items = list(self._metas.values())
        sliced = items[offset: offset + (limit or len(items))]
        return {"metadatas": sliced}

    def query(self, query_embeddings, n_results=5, where=None, include=None):
        if not self._docs:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        q = query_embeddings[0]

        def _match(meta):
            if where is None:
                return True
            if "$and" in where:
                return all(meta.get(list(f.keys())[0]) == list(f.values())[0] for f in where["$and"])
            k, v = list(where.items())[0]
            return meta.get(k) == v

        candidates = [i for i in self._docs.keys() if _match(self._metas.get(i, {}))]
        if not candidates:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        def _cosine_distance(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            na = math.sqrt(sum(x * x for x in a))
            nb = math.sqrt(sum(y * y for y in b))
            if na == 0 or nb == 0:
                return 1.0
            return 1.0 - (dot / (na * nb))

        scored = [(i, _cosine_distance(q, self._embeds[i])) for i in candidates]
        scored.sort(key=lambda t: t[1])
        top = scored[:n_results]

        return {
            "documents": [[self._docs[i] for i, _ in top]],
            "metadatas": [[self._metas[i] for i, _ in top]],
            "distances": [[d for _, d in top]],
        }


# ── Init ──────────────────────────────────────────────────

def init_chroma() -> None:
    """Appelé une fois au démarrage via lifespan FastAPI."""
    get_collection()


def is_dimension_mismatch_error(error: Exception) -> bool:
    """Retourne True si l'exception signale un mismatch de dimension Chroma."""
    return _DIMENSION_MISMATCH_RE.search(str(error)) is not None


def format_dimension_mismatch_error(error: Exception) -> str:
    """Formate un message lisible pour un mismatch de dimension."""
    match = _DIMENSION_MISMATCH_RE.search(str(error))
    if not match:
        return str(error)
    expected, got = match.group(1), match.group(2)
    return f"Collection Chroma incompatible avec le modèle d'embedding actuel (attendu {expected}, reçu {got})."


def get_client() -> chromadb.ClientAPI:
    global _client
    if os.getenv("FRAUDLY_CHROMA_IN_MEMORY", "0") == "1":
        if _client is None:
            logger.warning("[ChromaDB] FRAUDLY_CHROMA_IN_MEMORY=1 → fallback store in-memory activé.")
            _client = object()
        return _client

    if _client is None:
        if settings.CHROMA_HTTP_HOST:
            logger.info(
                f"[ChromaDB] Initialisation client HTTP sur "
                f"{settings.CHROMA_HTTP_HOST}:{settings.CHROMA_HTTP_PORT}..."
            )
            try:
                _client = chromadb.HttpClient(
                    host=settings.CHROMA_HTTP_HOST,
                    port=settings.CHROMA_HTTP_PORT,
                    ssl=settings.CHROMA_HTTP_SSL,
                )
            except Exception as error:
                logger.warning(
                    f"[ChromaDB] Serveur HTTP indisponible ({error})"
                )
                _client = chromadb.PersistentClient(
                    path=settings.CHROMA_PATH,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
        else:
            logger.info("[ChromaDB] Initialisation client persistant...")
            _client = chromadb.PersistentClient(
                path=settings.CHROMA_PATH,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        logger.info("[ChromaDB] Client prêt.")
    return _client


def get_collection():
    global _collection
    if _collection is None:
        if settings.VECTOR_STORE_BACKEND.lower() == "simple":
            _collection = _SimplePersistentCollection(settings.CHROMA_COLLECTION)
            logger.info(
                f"[SimpleStore] Collection prête — {_collection.count()} vecteurs persistés dans {_collection._store_path}"
            )
            return _collection

        if os.getenv("FRAUDLY_CHROMA_IN_MEMORY", "0") == "1":
            _collection = _InMemoryCollection(settings.CHROMA_COLLECTION)
            logger.info(f"[ChromaDB] Collection in-memory prête — {_collection.count()} vecteurs.")
            return _collection

        client = get_client()
        logger.info(f"[ChromaDB] Chargement collection '{settings.CHROMA_COLLECTION}'...")
        _collection = client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        # Avoid expensive count() at startup; this can delay API availability on large collections.
        logger.info("[ChromaDB] Collection prête.")
    return _collection


# ── Utils ─────────────────────────────────────────────────

def reset_collection() -> None:
    """Supprime et recrée la collection. Dev/debug uniquement."""
    global _collection
    if settings.VECTOR_STORE_BACKEND.lower() == "simple":
        _collection = _SimplePersistentCollection(settings.CHROMA_COLLECTION)
        if _collection._store_path.exists():
            _collection._store_path.unlink()
        _collection = _SimplePersistentCollection(settings.CHROMA_COLLECTION)
        logger.warning(f"[SimpleStore] Reset collection '{settings.CHROMA_COLLECTION}'")
        return

    client = get_client()
    logger.warning(f"[ChromaDB] Reset collection '{settings.CHROMA_COLLECTION}'")
    client.delete_collection(settings.CHROMA_COLLECTION)
    _collection = client.create_collection(
        name=settings.CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def get_distinct_course_ids() -> List[str]:
    """
    Retourne la liste triée des course_id distincts présents dans la collection.
    FIX : utilise la pagination (_PAGINATION_BATCH) pour éviter de charger
    l'intégralité des métadonnées en RAM sur les grandes collections.
    """
    col   = get_collection()
    total = col.count()
    seen: set = set()
    offset = 0

    while offset < total:
        batch = col.get(
            include=["metadatas"],
            limit=_PAGINATION_BATCH,
            offset=offset,
        )
        for meta in batch.get("metadatas", []):
            if meta and "course_id" in meta:
                seen.add(meta["course_id"])
        offset += _PAGINATION_BATCH

    return sorted(seen)


def count_chunks() -> int:
    return get_collection().count()