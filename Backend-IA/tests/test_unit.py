"""
Tests unitaires — RAG Pipeline Fraudly
=======================================
Couvre :
  - chunking_service  : découpage normal, overlap, paragraphe géant, page vide
  - embedding_service : query vide, préfixe E5, mismatch
  - rag_service       : build_rag_prompt (troncature), ingest_bytes (tmp cleanup),
                        search (collection vide, filtre where)
  - chroma_client     : get_distinct_course_ids paginé

Exécution :
    pytest tests/test_unit.py -v
"""

import os
import sys
import types
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

# ── Stub des modules lourds absents en CI ──────────────────────────────────────
# sentence_transformers, torch, chromadb, fitz, pytesseract, PIL, pydantic_settings
# sont stubbés pour que les tests tournent sans GPU ni dépendances système.

def _make_stub(name: str, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod

# pydantic_settings
ps = _make_stub("pydantic_settings")
class _BaseSettings:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)
ps.BaseSettings = _BaseSettings
sys.modules.setdefault("pydantic_settings", ps)

# sentence_transformers
st = _make_stub("sentence_transformers", SentenceTransformer=MagicMock)
sys.modules.setdefault("sentence_transformers", st)

# torch
torch_stub = _make_stub("torch", cuda=_make_stub("cuda", is_available=lambda: False))
sys.modules.setdefault("torch", torch_stub)

# numpy (utilisé dans embedding_service)
try:
    import numpy as np  # noqa: F401
except ImportError:
    np_stub = _make_stub("numpy", asarray=lambda x, **kw: x, float32=float)
    sys.modules.setdefault("numpy", np_stub)

# chromadb
chroma_stub = _make_stub(
    "chromadb",
    ClientAPI=MagicMock,
    PersistentClient=MagicMock,
)
chroma_stub.config = _make_stub("chromadb.config", Settings=MagicMock)
sys.modules.setdefault("chromadb", chroma_stub)
sys.modules.setdefault("chromadb.config", chroma_stub.config)

# fitz (PyMuPDF)
sys.modules.setdefault(
    "fitz",
    _make_stub("fitz", open=MagicMock, Matrix=MagicMock, Page=MagicMock, Document=MagicMock),
)

# pytesseract
sys.modules.setdefault("pytesseract", _make_stub("pytesseract", image_to_string=MagicMock, TesseractNotFoundError=Exception))

# PIL
pil_image_stub = _make_stub("PIL.Image", open=MagicMock, Image=type("_FakePILImage", (), {}))
pil_stub = _make_stub("PIL", Image=pil_image_stub)
sys.modules.setdefault("PIL", pil_stub)
sys.modules.setdefault("PIL.Image", pil_stub.Image)

# docx / pptx
sys.modules.setdefault("docx", _make_stub("docx", Document=MagicMock))
sys.modules.setdefault("pptx", _make_stub("pptx", Presentation=MagicMock))

# ── Config minimale ────────────────────────────────────────────────────────────
import importlib

# On patch settings avant d'importer les modules métier
mock_settings = MagicMock()
mock_settings.CHUNK_SIZE           = 100
mock_settings.CHUNK_OVERLAP        = 20
mock_settings.EMBEDDING_MODEL      = "intfloat/multilingual-e5-base"
mock_settings.EMBEDDING_DEVICE     = "cpu"
mock_settings.CHROMA_PATH          = "/tmp/test_chroma"
mock_settings.CHROMA_COLLECTION    = "test_col"
mock_settings.LLM_MODEL            = "claude-sonnet-4-6-20250514"
mock_settings.LLM_MAX_TOKENS       = 4096
mock_settings.PDF_IMAGE_STRATEGY   = "text_only"
mock_settings.OCR_LANG             = "fra+eng"
mock_settings.LOG_LEVEL            = "WARNING"

sys.modules["app.core.config"] = _make_stub("app.core.config", settings=mock_settings)
sys.modules["app.core.logger"] = _make_stub("app.core.logger", get_logger=lambda n: MagicMock())

# Import des modules sous test
import importlib.util, pathlib

_project_root = pathlib.Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

def _load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

_base = str(_project_root)

chunking   = _load(f"{_base}/app/services/chunking_service.py",  "chunking_service")
embedding  = _load(f"{_base}/app/services/embedding_service.py", "embedding_service")
rag        = _load(f"{_base}/app/services/rag_service.py",       "rag_service")
chroma_cli = _load(f"{_base}/app/db/chroma_client.py",           "chroma_client")


# ══════════════════════════════════════════════════════════════════════════════
# 1. CHUNKING SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class TestChunkingService:

    def _pages(self, text: str, page_number: int = 1):
        return [{"text": text, "page_number": page_number}]

    def test_single_short_paragraph_produces_one_chunk(self):
        pages  = self._pages("Bonjour le monde.")
        result = chunking.chunk_pages(pages, "c1", "ch1", "test.pdf")
        assert len(result) == 1
        assert result[0]["text"] == "Bonjour le monde."

    def test_metadata_fields_are_complete(self):
        pages  = self._pages("Un texte court.", page_number=3)
        result = chunking.chunk_pages(pages, "cours_42", "chap_7", "doc.pdf")
        meta   = result[0]["metadata"]
        assert meta["course_id"]   == "cours_42"
        assert meta["chapter_id"]  == "chap_7"
        assert meta["source_file"] == "doc.pdf"
        assert meta["page"]        == 3

    def test_two_paragraphs_stay_in_one_chunk_if_under_limit(self):
        # CHUNK_SIZE = 100 → "Para A." + "\n\n" + "Para B." = 16 chars → 1 chunk
        pages  = self._pages("Para A.\n\nPara B.")
        result = chunking.chunk_pages(pages, "c1", "ch1", "f.pdf")
        assert len(result) == 1
        assert "Para A." in result[0]["text"]
        assert "Para B." in result[0]["text"]

    def test_overflow_creates_new_chunk_with_overlap(self):
        # Deux paragraphes qui dépassent CHUNK_SIZE=100 ensemble
        para_a = "A" * 60
        para_b = "B" * 60
        pages  = self._pages(f"{para_a}\n\n{para_b}")
        result = chunking.chunk_pages(pages, "c1", "ch1", "f.pdf")
        assert len(result) == 2
        # Le 2e chunk doit contenir les derniers CHUNK_OVERLAP=20 chars de para_a (overlap)
        assert result[1]["text"].startswith("A" * 20)

    def test_giant_paragraph_is_split(self):
        # Paragraphe unique de 350 chars > CHUNK_SIZE=100
        giant  = "X" * 350
        pages  = self._pages(giant)
        result = chunking.chunk_pages(pages, "c1", "ch1", "f.pdf")
        # Doit produire plusieurs chunks, aucun ne dépasse CHUNK_SIZE
        assert len(result) > 1
        for chunk in result:
            assert len(chunk["text"]) <= mock_settings.CHUNK_SIZE

    def test_empty_page_produces_no_chunk(self):
        pages  = self._pages("   \n\n   ")
        result = chunking.chunk_pages(pages, "c1", "ch1", "f.pdf")
        assert result == []

    def test_multiple_pages_each_chunked(self):
        pages = [
            {"text": "Page un contenu court.", "page_number": 1},
            {"text": "Page deux contenu court.", "page_number": 2},
        ]
        result = chunking.chunk_pages(pages, "c1", "ch1", "f.pdf")
        assert len(result) == 2
        assert result[0]["metadata"]["page"] == 1
        assert result[1]["metadata"]["page"] == 2


# ══════════════════════════════════════════════════════════════════════════════
# 2. EMBEDDING SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class TestEmbeddingService:

    def _mock_model(self, return_value):
        """Retourne un faux SentenceTransformer dont encode() retourne return_value."""
        import numpy as np
        m = MagicMock()
        m.encode.return_value = np.array(return_value, dtype=np.float32)
        return m

    def test_embed_query_raises_on_empty_string(self):
        with pytest.raises(ValueError, match="vide"):
            embedding.embed_query("")

    def test_embed_query_raises_on_whitespace_only(self):
        with pytest.raises(ValueError):
            embedding.embed_query("   ")

    def test_embed_query_adds_e5_prefix(self):
        import numpy as np
        mock_model = self._mock_model([[0.1, 0.2, 0.3]])
        embedding._model = mock_model
        embedding.embed_query("test query")
        call_arg = mock_model.encode.call_args[0][0]
        assert call_arg.startswith("query: ")
        embedding._model = None

    def test_embed_chunks_adds_passage_prefix(self):
        import numpy as np
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2]], dtype=np.float32)
        embedding._model = mock_model
        embedding.embed_chunks(["un chunk de texte"])
        call_args = mock_model.encode.call_args[0][0]
        assert all(t.startswith("passage: ") for t in call_args)
        embedding._model = None

    def test_embed_chunks_empty_list_returns_empty(self):
        result = embedding.embed_chunks([])
        assert result == []

    def test_embed_chunks_mismatch_raises(self):
        import numpy as np
        mock_model = MagicMock()
        # encode retourne 1 vecteur pour 2 textes → mismatch
        mock_model.encode.return_value = np.array([[0.1, 0.2]], dtype=np.float32)
        embedding._model = mock_model
        with pytest.raises(ValueError, match="[Mm]ismatch"):
            embedding.embed_chunks(["texte 1", "texte 2"])
        embedding._model = None

    def test_no_e5_prefix_for_non_e5_model(self):
        import numpy as np
        original = mock_settings.EMBEDDING_MODEL
        mock_settings.EMBEDDING_MODEL = "BAAI/bge-m3"
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2]], dtype=np.float32)
        embedding._model = mock_model
        embedding.embed_query("ma requête")
        call_arg = mock_model.encode.call_args[0][0]
        assert not call_arg.startswith("query: ")
        mock_settings.EMBEDDING_MODEL = original
        embedding._model = None


# ══════════════════════════════════════════════════════════════════════════════
# 3. RAG SERVICE — build_rag_prompt
# ══════════════════════════════════════════════════════════════════════════════

class TestBuildRagPrompt:

    def _make_chunk(self, content: str, score: float = 0.9, page: int = 1) -> object:
        c = MagicMock()
        c.content     = content
        c.score       = score
        c.source_file = "cours_fraude.pdf"
        c.page        = page
        return c

    def test_no_chunks_returns_aucun_doc(self):
        prompt = rag.build_rag_prompt("Qu'est-ce que la fraude ?", [])
        assert "Aucun document pertinent" in prompt

    def test_prompt_contains_question(self):
        prompt = rag.build_rag_prompt("Ma question ?", [self._make_chunk("Contenu.")])
        assert "Ma question ?" in prompt

    def test_prompt_contains_chunk_content(self):
        prompt = rag.build_rag_prompt("Question ?", [self._make_chunk("Réponse clé.")])
        assert "Réponse clé." in prompt

    def test_prompt_truncates_at_max_context_chars(self):
        # Crée suffisamment de chunks pour dépasser MAX_CONTEXT_CHARS
        big_chunks = [self._make_chunk("Z" * 3000, page=i) for i in range(10)]
        prompt     = rag.build_rag_prompt("Question longue ?", big_chunks)
        # Le contexte injecté ne doit pas dépasser MAX_CONTEXT_CHARS + overhead headers
        assert len(prompt) < rag.MAX_CONTEXT_CHARS + 500

    def test_prompt_contains_source_citation(self):
        prompt = rag.build_rag_prompt("?", [self._make_chunk("Texte.", page=5)])
        assert "[Source 1]" in prompt
        assert "cours_fraude.pdf" in prompt

    def test_prompt_has_strict_rules(self):
        prompt = rag.build_rag_prompt("?", [])
        assert "RÈGLES STRICTES" in prompt
        assert "inventer" in prompt.lower()


# ══════════════════════════════════════════════════════════════════════════════
# 4. RAG SERVICE — ingest_bytes (gestion fichier temporaire)
# ══════════════════════════════════════════════════════════════════════════════

class TestIngestBytes:

    def _mock_ingest_file(self, *args, **kwargs):
        resp = MagicMock()
        resp.status = "ok"
        return resp

    def test_tmp_file_deleted_on_success(self):
        created_paths = []

        class FakeTmp:
            name = "/tmp/fake_test_file.pdf"
            def write(self, b): pass
            def __enter__(self): created_paths.append(self.name); return self
            def __exit__(self, *a): pass

        with patch("rag_service.tempfile.NamedTemporaryFile", return_value=FakeTmp()), \
             patch("rag_service.os.path.exists", return_value=True), \
             patch("rag_service.os.unlink") as mock_unlink, \
             patch("rag_service.ingest_file", side_effect=self._mock_ingest_file):
            rag.ingest_bytes(b"data", "f.pdf", "c1", "ch1", MagicMock(value="pdf"))
            mock_unlink.assert_called_once_with("/tmp/fake_test_file.pdf")

    def test_tmp_file_deleted_even_on_ingest_error(self):
        class FakeTmp:
            name = "/tmp/fake_err_file.pdf"
            def write(self, b): pass
            def __enter__(self): return self
            def __exit__(self, *a): pass

        with patch("rag_service.tempfile.NamedTemporaryFile", return_value=FakeTmp()), \
             patch("rag_service.os.path.exists", return_value=True), \
             patch("rag_service.os.unlink") as mock_unlink, \
             patch("rag_service.ingest_file", side_effect=RuntimeError("boom")):
            with pytest.raises(RuntimeError):
                rag.ingest_bytes(b"data", "f.pdf", "c1", "ch1", MagicMock(value="pdf"))
            mock_unlink.assert_called_once()

    def test_no_unlink_if_tmp_path_never_assigned(self):
        """Si NamedTemporaryFile lève avant d'assigner tmp_path, pas de NameError."""
        with patch("rag_service.tempfile.NamedTemporaryFile", side_effect=OSError("no space")), \
             patch("rag_service.os.unlink") as mock_unlink:
            with pytest.raises(OSError):
                rag.ingest_bytes(b"", "f.pdf", "c1", "ch1", MagicMock(value="pdf"))
            mock_unlink.assert_not_called()


# ══════════════════════════════════════════════════════════════════════════════
# 5. RAG SERVICE — search()
# ══════════════════════════════════════════════════════════════════════════════

class TestSearch:

    def _collection(self, count=10, query_result=None):
        col = MagicMock()
        col.count.return_value = count
        col.query.return_value = query_result or {
            "documents": [["Doc pertinent sur la fraude documentaire."]],
            "metadatas": [[ {"course_id": "c1", "chapter_id": "ch1", "source_file": "f.pdf", "page": 2} ]],
            "distances": [[0.12]],
        }
        return col

    def test_empty_collection_returns_empty_response(self):
        with patch("rag_service.get_collection", return_value=self._collection(count=0)):
            result = rag.search("fraude")
        assert result.total_found == 0
        assert result.chunks == []

    def test_search_returns_chunks_with_correct_score(self):
        with patch("rag_service.get_collection", return_value=self._collection()), \
             patch("rag_service.embed_query", return_value=[0.1] * 768):
            result = rag.search("fraude documentaire", course_id="c1")
        assert result.total_found == 1
        assert result.chunks[0].score == round(1.0 - 0.12, 4)

    def test_search_filters_by_course_id(self):
        col = self._collection()
        with patch("rag_service.get_collection", return_value=col), \
             patch("rag_service.embed_query", return_value=[0.1] * 768):
            rag.search("fraude", course_id="c1")
        call_kwargs = col.query.call_args[1]
        assert call_kwargs["where"] == {"course_id": "c1"}

    def test_search_filters_by_course_and_chapter(self):
        col = self._collection()
        with patch("rag_service.get_collection", return_value=col), \
             patch("rag_service.embed_query", return_value=[0.1] * 768):
            rag.search("fraude", course_id="c1", chapter_id="ch1")
        call_kwargs = col.query.call_args[1]
        assert "$and" in call_kwargs["where"]

    def test_search_filters_by_multiple_chapters(self):
        col = self._collection()
        with patch("rag_service.get_collection", return_value=col), \
             patch("rag_service.embed_query", return_value=[0.1] * 768):
            rag.search("fraude", course_id="c1", chapter_ids=["ch1", "ch2"])
        assert col.query.call_count == 2
        first_where = col.query.call_args_list[0][1]["where"]
        second_where = col.query.call_args_list[1][1]["where"]
        assert first_where == {"$and": [{"course_id": "c1"}, {"chapter_id": "ch1"}]}
        assert second_where == {"$and": [{"course_id": "c1"}, {"chapter_id": "ch2"}]}

    def test_search_no_filter_when_no_ids(self):
        col = self._collection()
        with patch("rag_service.get_collection", return_value=col), \
             patch("rag_service.embed_query", return_value=[0.1] * 768):
            rag.search("fraude")
        call_kwargs = col.query.call_args[1]
        assert call_kwargs["where"] is None

    def test_search_does_not_raise_on_chroma_error(self):
        col = MagicMock()
        col.count.return_value = 5
        col.query.side_effect  = RuntimeError("ChromaDB down")
        with patch("rag_service.get_collection", return_value=col), \
             patch("rag_service.embed_query", return_value=[0.1] * 768):
            result = rag.search("fraude")
        assert result.total_found == 0


# ══════════════════════════════════════════════════════════════════════════════
# 6. CHROMA CLIENT — get_distinct_course_ids (pagination)
# ══════════════════════════════════════════════════════════════════════════════

class TestChromaClient:

    def _fake_col(self, total: int, batch_size: int):
        """Simule une collection de `total` chunks paginée par batch_size."""
        all_metas = [{"course_id": f"course_{i % 5}"} for i in range(total)]

        def _get(include=None, limit=None, offset=0):
            return {"metadatas": all_metas[offset : offset + (limit or total)]}

        col = MagicMock()
        col.count.return_value = total
        col.get.side_effect    = _get
        return col

    def test_returns_sorted_distinct_ids(self):
        col = self._fake_col(total=50, batch_size=10)
        chroma_cli._PAGINATION_BATCH = 10
        with patch("chroma_client.get_collection", return_value=col):
            result = chroma_cli.get_distinct_course_ids()
        assert result == sorted(set(f"course_{i % 5}" for i in range(50)))

    def test_pagination_called_multiple_times_for_large_collection(self):
        col = self._fake_col(total=25, batch_size=10)
        chroma_cli._PAGINATION_BATCH = 10
        with patch("chroma_client.get_collection", return_value=col):
            chroma_cli.get_distinct_course_ids()
        # 25 chunks / 10 per page → 3 appels (0, 10, 20)
        assert col.get.call_count == 3

    def test_empty_collection_returns_empty_list(self):
        col = MagicMock()
        col.count.return_value = 0
        col.get.return_value   = {"metadatas": []}
        with patch("chroma_client.get_collection", return_value=col):
            result = chroma_cli.get_distinct_course_ids()
        assert result == []