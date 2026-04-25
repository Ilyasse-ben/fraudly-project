import asyncio
import hashlib
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api import knowledge
from app.schemas.common import IngestStatus
from app.schemas.rag_schema import IngestResponse


class _FakeUploadFile:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


class TestIngestApi:
    def test_ingest_success_returns_resource_and_version(self, monkeypatch):
        file_content = b"pdf content"
        fake_file = _FakeUploadFile("cours.pdf", file_content)

        mock_get_job = MagicMock(return_value=None)
        mock_upsert = MagicMock(return_value={})
        mock_ingest = MagicMock(
            return_value=IngestResponse(
                filename="cours.pdf",
                course_id="c1",
                chapter_id="ch1",
                pages_processed=2,
                chunks_indexed=8,
                status=IngestStatus.OK,
            )
        )
        monkeypatch.setattr(knowledge, "get_ingestion_job", mock_get_job)
        monkeypatch.setattr(knowledge, "upsert_ingestion_job", mock_upsert)
        monkeypatch.setattr(knowledge, "ingest_bytes", mock_ingest)

        result = asyncio.run(
            knowledge.ingest_document(
                file=fake_file,
                course_id="c1",
                chapter_id="ch1",
                resource_id="res_1",
                version="v1",
            )
        )

        assert result.resource_id == "res_1"
        assert result.version == "v1"
        assert result.idempotent_hit is False
        assert result.status == IngestStatus.OK
        assert result.chunks_indexed == 8
        mock_ingest.assert_called_once()
        mock_upsert.assert_called_once()

    def test_ingest_idempotent_hit_skips_reindex(self, monkeypatch):
        file_content = b"same content"
        fake_file = _FakeUploadFile("cours.pdf", file_content)
        digest = hashlib.sha256(file_content).hexdigest()

        mock_get_job = MagicMock(
            return_value={
                "resource_id": "res_2",
                "version": "v1",
                "filename": "cours.pdf",
                "course_id": "c1",
                "chapter_id": "ch1",
                "content_hash": digest,
                "status": "ok",
                "pages_processed": 1,
                "chunks_indexed": 5,
                "message": None,
                "created_at": "2026-04-22T10:00:00Z",
                "updated_at": "2026-04-22T10:00:00Z",
            }
        )
        mock_ingest = MagicMock()
        monkeypatch.setattr(knowledge, "get_ingestion_job", mock_get_job)
        monkeypatch.setattr(knowledge, "ingest_bytes", mock_ingest)

        result = asyncio.run(
            knowledge.ingest_document(
                file=fake_file,
                course_id="c1",
                chapter_id="ch1",
                resource_id="res_2",
                version="v1",
            )
        )

        assert result.idempotent_hit is True
        assert result.status == IngestStatus.OK
        mock_ingest.assert_not_called()

    def test_ingest_conflict_on_same_resource_version_different_content(self, monkeypatch):
        file_content = b"new content"
        fake_file = _FakeUploadFile("cours.pdf", file_content)

        mock_get_job = MagicMock(
            return_value={
                "resource_id": "res_3",
                "version": "v1",
                "filename": "cours.pdf",
                "course_id": "c1",
                "chapter_id": "ch1",
                "content_hash": "different_hash",
                "status": "ok",
                "pages_processed": 1,
                "chunks_indexed": 5,
                "message": None,
                "created_at": "2026-04-22T10:00:00Z",
                "updated_at": "2026-04-22T10:00:00Z",
            }
        )
        monkeypatch.setattr(knowledge, "get_ingestion_job", mock_get_job)

        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                knowledge.ingest_document(
                    file=fake_file,
                    course_id="c1",
                    chapter_id="ch1",
                    resource_id="res_3",
                    version="v1",
                )
            )

        assert exc.value.status_code == 409
