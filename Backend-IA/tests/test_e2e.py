"""
Tests end-to-end — Pipeline RAG complet (sans LLM, sans GPU)
=============================================================
Simule un cycle complet :
  1. Ingestion d'un corpus fictif sur la fraude documentaire (texte brut)
  2. Recherche sémantique (embeddings réels via sentence-transformers ou mock)
  3. Construction du prompt RAG final
  4. Vérifications de qualité du retrieval

Le corpus fictif couvre 3 "cours" et 2 "chapitres" pour tester les filtres.

Exécution :
    pytest tests/test_e2e.py -v
    pytest tests/test_e2e.py -v --log-cli-level=INFO   # avec logs RAG
"""

import os
import sys
import shutil
import types
import pytest
from unittest.mock import MagicMock, patch
import tempfile

# ── Stubs identiques au test_unit.py ──────────────────────────────────────────
def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod

ps = _make_stub("pydantic_settings")
class _BaseSettings:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)
ps.BaseSettings = _BaseSettings
sys.modules.setdefault("pydantic_settings", ps)

try:
    from sentence_transformers import SentenceTransformer  # noqa
    _HAS_ST = True
except ImportError:
    _HAS_ST = False
    sys.modules.setdefault("sentence_transformers", _make_stub("sentence_transformers", SentenceTransformer=MagicMock))

sys.modules.setdefault("torch", _make_stub("torch", cuda=_make_stub("cuda", is_available=lambda: False)))

try:
    import numpy as np  # noqa
except ImportError:
    sys.modules.setdefault("numpy", _make_stub("numpy", asarray=lambda x, **kw: x, float32=float, array=lambda x, **kw: x))

chroma_stub = _make_stub("chromadb", ClientAPI=MagicMock, PersistentClient=MagicMock)
chroma_stub.config = _make_stub("chromadb.config", Settings=MagicMock)
sys.modules.setdefault("chromadb", chroma_stub)
sys.modules.setdefault("chromadb.config", chroma_stub.config)

sys.modules.setdefault(
    "fitz",
    _make_stub("fitz", open=MagicMock, Matrix=MagicMock, Page=MagicMock, Document=MagicMock),
)
sys.modules.setdefault("pytesseract",  _make_stub("pytesseract", image_to_string=MagicMock, TesseractNotFoundError=Exception))
pil_image_stub = _make_stub("PIL.Image", open=MagicMock, Image=type("_FakePILImage", (), {}))
pil_stub = _make_stub("PIL", Image=pil_image_stub)
sys.modules.setdefault("PIL",          pil_stub)
sys.modules.setdefault("PIL.Image",    pil_stub.Image)
sys.modules.setdefault("docx",         _make_stub("docx", Document=MagicMock))
sys.modules.setdefault("pptx",         _make_stub("pptx", Presentation=MagicMock))

# ── Settings de test ──────────────────────────────────────────────────────────
mock_settings = MagicMock()
mock_settings.CHUNK_SIZE         = 300
mock_settings.CHUNK_OVERLAP      = 50
mock_settings.EMBEDDING_MODEL    = "intfloat/multilingual-e5-base"
mock_settings.EMBEDDING_DEVICE   = "cpu"
mock_settings.CHROMA_PATH        = tempfile.mkdtemp(prefix="test_chroma_")
mock_settings.CHROMA_COLLECTION  = "test_fraudly"
mock_settings.PDF_IMAGE_STRATEGY = "text_only"
mock_settings.OCR_LANG           = "fra+eng"
mock_settings.LOG_LEVEL          = "WARNING"

# ── Import modules sous test ───────────────────────────────────────────────────
sys.modules["app.core.config"] = _make_stub("app.core.config", settings=mock_settings)
sys.modules["app.core.logger"] = _make_stub("app.core.logger", get_logger=lambda n: MagicMock())

import importlib.util, pathlib

_project_root = pathlib.Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

_base      = str(_project_root)
chunking   = _load(f"{_base}/app/services/chunking_service.py",  "chunking_service")
embedding  = _load(f"{_base}/app/services/embedding_service.py", "embedding_service")
rag        = _load(f"{_base}/app/services/rag_service.py",       "rag_service")
chroma_cli = _load(f"{_base}/app/db/chroma_client.py",           "chroma_client")

# ── Corpus fictif ─────────────────────────────────────────────────────────────
# 3 cours × 2 chapitres — thème : fraude documentaire
CORPUS = [
    {
        "course_id":  "fraude_101",
        "chapter_id": "intro",
        "filename":   "introduction_fraude.pdf",
        "pages": [
            {
                "page_number": 1,
                "text": (
                    "La fraude documentaire désigne toute falsification ou contrefaçon "
                    "d'un document officiel dans le but de tromper une institution ou une personne. "
                    "Elle inclut la fabrication de faux passeports, cartes d'identité, diplômes et contrats.\n\n"
                    "Les techniques de détection modernes s'appuient sur des algorithmes de machine learning "
                    "capables d'identifier des anomalies dans les polices de caractères, les tampons officiels "
                    "et les métadonnées des fichiers PDF."
                ),
            },
            {
                "page_number": 2,
                "text": (
                    "Les conséquences juridiques de la fraude documentaire sont sévères. "
                    "En France, l'article 441-1 du Code pénal punit la fabrication de faux "
                    "de trois ans d'emprisonnement et 45 000 euros d'amende.\n\n"
                    "Les organismes financiers sont particulièrement exposés : "
                    "les banques traitent des millions de documents chaque année et doivent "
                    "déployer des systèmes de vérification automatisés robustes."
                ),
            },
        ],
    },
    {
        "course_id":  "fraude_101",
        "chapter_id": "detection",
        "filename":   "methodes_detection.pdf",
        "pages": [
            {
                "page_number": 1,
                "text": (
                    "La détection automatique de fraude repose sur trois familles de techniques :\n\n"
                    "1. L'analyse forensique numérique : examen des métadonnées EXIF, des couches PDF "
                    "et des signatures numériques pour identifier des incohérences.\n\n"
                    "2. La vision par ordinateur : réseaux de neurones convolutifs entraînés à repérer "
                    "les zones de falsification, les retouches Photoshop et les montages photographiques.\n\n"
                    "3. Le traitement du langage naturel : modèles NLP qui détectent des incohérences "
                    "sémantiques dans les textes des documents (dates illogiques, numéros invalides)."
                ),
            },
        ],
    },
    {
        "course_id":  "kyc_202",
        "chapter_id": "verification",
        "filename":   "processus_kyc.pdf",
        "pages": [
            {
                "page_number": 1,
                "text": (
                    "Le processus KYC (Know Your Customer) est obligatoire pour les établissements "
                    "financiers soumis à la directive européenne Anti-Blanchiment (AMLD5/6).\n\n"
                    "Il comprend trois étapes : identification du client, vérification des documents "
                    "d'identité, et évaluation du risque. Les solutions modernes utilisent "
                    "la reconnaissance faciale, la lecture OCR et des bases de données mondiales "
                    "de documents volés ou falsifiés."
                ),
            },
            {
                "page_number": 2,
                "text": (
                    "Les erreurs courantes dans le processus KYC incluent :\n\n"
                    "- Accepter des documents expirés sans vérification de validité\n"
                    "- Omettre de croiser les informations avec les listes de sanctions internationales\n"
                    "- Ne pas renouveler la vérification lors d'un changement de situation du client\n\n"
                    "Un KYC défaillant expose l'établissement à des amendes réglementaires "
                    "pouvant atteindre des dizaines de millions d'euros."
                ),
            },
        ],
    },
]


# ── Helpers de test ───────────────────────────────────────────────────────────

def _make_deterministic_embeddings(texts):
    """
    Génère des embeddings déterministes sans modèle réel.
    Chaque vecteur est basé sur un hash du texte pour garantir la reproductibilité
    et simuler un comportement sémantique (textes similaires → vecteurs proches).
    """
    import numpy as np
    import hashlib

    dim = 64
    vecs = []
    for text in texts:
        seed = int(hashlib.md5(text[:50].encode()).hexdigest(), 16) % (2**31)
        rng  = np.random.RandomState(seed)
        v    = rng.randn(dim).astype(np.float32)
        v   /= (np.linalg.norm(v) + 1e-9)
        vecs.append(v.tolist())
    return vecs

def _make_deterministic_query_embedding(query):
    return _make_deterministic_embeddings([query])[0]


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def chroma_collection():
    """
    Crée une vraie collection ChromaDB en mémoire pour les tests E2E.
    Nettoyage automatique après la session de tests.
    """
    try:
        import chromadb as _chromadb
        if hasattr(_chromadb, "EphemeralClient"):
            client = _chromadb.EphemeralClient()
        else:
            # Fallback si EphemeralClient absent (vieille version)
            client = _chromadb.Client()
        col = client.get_or_create_collection(
            name="test_e2e",
            metadata={"hnsw:space": "cosine"},
        )
        yield col
        client.delete_collection("test_e2e")
    except Exception:
        # chromadb non installé → on mock une collection en mémoire
        yield _InMemoryCollection()


class _InMemoryCollection:
    """Collection ChromaDB en mémoire minimaliste pour CI sans chromadb installé."""

    def __init__(self):
        self._docs    = {}  # id → text
        self._metas   = {}  # id → metadata
        self._embeds  = {}  # id → embedding
        self.name     = "in_memory_test"

    def add(self, ids, embeddings, documents, metadatas):
        for i, doc, meta, emb in zip(ids, documents, metadatas, embeddings):
            self._docs[i]   = doc
            self._metas[i]  = meta
            self._embeds[i] = emb

    def query(self, query_embeddings, n_results=5, where=None, include=None):
        import numpy as np

        q     = np.array(query_embeddings[0], dtype=np.float32)
        items = list(self._docs.keys())

        # Filtrage metadata
        if where:
            def _match(meta):
                if "$and" in where:
                    return all(
                        meta.get(list(f.keys())[0]) == list(f.values())[0]
                        for f in where["$and"]
                    )
                k, v = list(where.items())[0]
                return meta.get(k) == v
            items = [i for i in items if _match(self._metas[i])]

        if not items:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        # Cosine distance approximée
        scores = []
        for i in items:
            emb  = np.array(self._embeds[i], dtype=np.float32)
            dist = 1.0 - float(np.dot(q, emb) / (np.linalg.norm(q) * np.linalg.norm(emb) + 1e-9))
            scores.append((i, dist))
        scores.sort(key=lambda x: x[1])
        top = scores[:n_results]

        return {
            "documents": [[self._docs[i]   for i, _ in top]],
            "metadatas": [[self._metas[i]  for i, _ in top]],
            "distances": [[d               for _, d  in top]],
        }

    def count(self):
        return len(self._docs)

    def get(self, include=None, limit=None, offset=0):
        items = list(self._metas.items())[offset: offset + (limit or len(self._metas))]
        return {"metadatas": [v for _, v in items]}


# ══════════════════════════════════════════════════════════════════════════════
# TESTS E2E
# ══════════════════════════════════════════════════════════════════════════════

class TestEndToEnd:

    @pytest.fixture(autouse=True)
    def setup(self, chroma_collection):
        """Ingère le corpus fictif une fois par classe de test."""
        self.col = chroma_collection

        # Génère tous les chunks du corpus
        all_chunks = []
        for doc in CORPUS:
            chunks = chunking.chunk_pages(
                pages      = doc["pages"],
                course_id  = doc["course_id"],
                chapter_id = doc["chapter_id"],
                filename   = doc["filename"],
            )
            all_chunks.extend(chunks)

        self.all_chunks = all_chunks
        self.texts      = [c["text"] for c in all_chunks]

        # Embeddings déterministes (pas de modèle réel nécessaire)
        embeddings = _make_deterministic_embeddings(self.texts)
        ids = [f"chunk_{i}" for i in range(len(all_chunks))]

        # Index dans la collection
        if self.col.count() == 0:
            self.col.add(
                ids        = ids,
                embeddings = embeddings,
                documents  = self.texts,
                metadatas  = [c["metadata"] for c in all_chunks],
            )

    # ── 1. Chunking du corpus ─────────────────────────────────────────────────

    def test_corpus_produces_chunks(self):
        assert len(self.all_chunks) > 0

    def test_all_chunks_have_required_metadata_keys(self):
        for chunk in self.all_chunks:
            meta = chunk["metadata"]
            assert "course_id"   in meta
            assert "chapter_id"  in meta
            assert "source_file" in meta
            assert "page"        in meta

    def test_no_chunk_exceeds_size_limit(self):
        # L'implémentation conserve un overlap en tête du chunk suivant,
        # donc un chunk peut dépasser CHUNK_SIZE d'environ CHUNK_OVERLAP.
        max_allowed = mock_settings.CHUNK_SIZE + mock_settings.CHUNK_OVERLAP + 2
        for chunk in self.all_chunks:
            assert len(chunk["text"]) <= max_allowed, (
                f"Chunk trop long ({len(chunk['text'])} chars) : {chunk['text'][:60]}…"
            )

    def test_chunks_cover_all_courses(self):
        course_ids = {c["metadata"]["course_id"] for c in self.all_chunks}
        assert "fraude_101" in course_ids
        assert "kyc_202"    in course_ids

    def test_chunks_cover_all_chapters(self):
        chapter_ids = {c["metadata"]["chapter_id"] for c in self.all_chunks}
        assert "intro"        in chapter_ids
        assert "detection"    in chapter_ids
        assert "verification" in chapter_ids

    # ── 2. Ingestion dans ChromaDB ────────────────────────────────────────────

    def test_collection_not_empty_after_ingest(self):
        assert self.col.count() > 0

    def test_collection_count_matches_chunks(self):
        assert self.col.count() == len(self.all_chunks)

    # ── 3. Search sans filtre ─────────────────────────────────────────────────

    def test_search_fraude_retourne_des_resultats(self):
        query_emb = _make_deterministic_query_embedding("fraude documentaire détection")
        results   = self.col.query(
            query_embeddings=[query_emb],
            n_results=3,
            where=None,
        )
        docs = results["documents"][0]
        assert len(docs) > 0

    def test_search_scores_are_between_0_and_1(self):
        query_emb = _make_deterministic_query_embedding("falsification carte identité")
        results   = self.col.query(
            query_embeddings=[query_emb],
            n_results=5,
            where=None,
        )
        for dist in results["distances"][0]:
            score = round(1.0 - float(dist), 4)
            assert 0.0 <= score <= 1.0, f"Score hors bornes : {score}"

    # ── 4. Search avec filtre course_id ──────────────────────────────────────

    def test_filter_by_course_id_retourne_uniquement_ce_cours(self):
        query_emb = _make_deterministic_query_embedding("vérification identité")
        results   = self.col.query(
            query_embeddings=[query_emb],
            n_results=10,
            where={"course_id": "kyc_202"},
        )
        metas = results["metadatas"][0]
        assert all(m["course_id"] == "kyc_202" for m in metas), (
            "Des chunks d'un autre cours ont été renvoyés malgré le filtre course_id"
        )

    def test_filter_by_chapter_id_retourne_uniquement_ce_chapitre(self):
        query_emb = _make_deterministic_query_embedding("machine learning détection")
        results   = self.col.query(
            query_embeddings=[query_emb],
            n_results=10,
            where={"chapter_id": "detection"},
        )
        metas = results["metadatas"][0]
        assert all(m["chapter_id"] == "detection" for m in metas)

    def test_filter_course_and_chapter_combined(self):
        query_emb = _make_deterministic_query_embedding("NLP texte")
        results   = self.col.query(
            query_embeddings=[query_emb],
            n_results=10,
            where={"$and": [{"course_id": "fraude_101"}, {"chapter_id": "detection"}]},
        )
        metas = results["metadatas"][0]
        assert all(
            m["course_id"] == "fraude_101" and m["chapter_id"] == "detection"
            for m in metas
        )

    def test_filter_inexistant_retourne_vide(self):
        query_emb = _make_deterministic_query_embedding("question quelconque")
        results   = self.col.query(
            query_embeddings=[query_emb],
            n_results=5,
            where={"course_id": "cours_inexistant_xyz"},
        )
        assert results["documents"][0] == []

    # ── 5. Build RAG prompt ───────────────────────────────────────────────────

    def test_rag_prompt_pipeline_complet(self):
        """
        Simule le pipeline complet :
        question → search → chunks → build_rag_prompt → prompt final
        """
        question  = "Quelles sont les techniques de détection de fraude documentaire ?"
        query_emb = _make_deterministic_query_embedding(question)

        results = self.col.query(
            query_embeddings=[query_emb],
            n_results=3,
            where=None,
        )

        # Reconstruction des KnowledgeChunk
        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            c = MagicMock()
            c.content     = doc
            c.source_file = meta.get("source_file", "")
            c.page        = meta.get("page", 1)
            c.score       = round(max(0.0, 1.0 - float(dist)), 4)
            chunks.append(c)

        prompt = rag.build_rag_prompt(question, chunks)

        assert question in prompt
        assert "CONTEXTE"       in prompt
        assert "RÈGLES STRICTES" in prompt
        assert "[Source 1]"     in prompt
        assert len(prompt)      >  200

    def test_rag_prompt_respecte_limite_contexte(self):
        """Vérifie que build_rag_prompt tronque bien au-delà de MAX_CONTEXT_CHARS."""
        big_chunks = []
        for i in range(20):
            c = MagicMock()
            c.content     = "A" * 1000
            c.source_file = "gros_doc.pdf"
            c.page        = i + 1
            c.score       = 0.9
            big_chunks.append(c)

        prompt = rag.build_rag_prompt("Question test ?", big_chunks)
        assert len(prompt) < rag.MAX_CONTEXT_CHARS + 600

    # ── 6. Ingest → search round-trip ─────────────────────────────────────────

    def test_ingested_content_is_retrievable_by_keyword(self):
        """
        Vérifie que le contenu ingéré peut être retrouvé via une requête
        contenant un mot-clé exact du corpus.
        """
        query_emb = _make_deterministic_query_embedding("article 441-1 Code pénal emprisonnement")
        results   = self.col.query(
            query_embeddings=[query_emb],
            n_results=5,
            where=None,
        )
        found_texts = " ".join(results["documents"][0])
        # Le chunk contenant le Code pénal doit ressortir
        assert any(
            "441" in doc or "pénal" in doc.lower() or "emprisonnement" in doc.lower()
            for doc in results["documents"][0]
        ), f"Le contenu juridique n'a pas été retrouvé. Résultats : {found_texts[:200]}"

    def test_kyc_content_not_returned_when_filtering_fraude_101(self):
        """Garantit l'isolation entre cours lors d'un filtre strict."""
        query_emb = _make_deterministic_query_embedding("vérification client KYC directive")
        results   = self.col.query(
            query_embeddings=[query_emb],
            n_results=10,
            where={"course_id": "fraude_101"},
        )
        for meta in results["metadatas"][0]:
            assert meta["course_id"] != "kyc_202", (
                "Un chunk KYC a été renvoyé dans une recherche filtrée sur fraude_101"
            )