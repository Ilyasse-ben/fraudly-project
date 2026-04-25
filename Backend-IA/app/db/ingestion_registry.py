import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import json

from app.core.config import settings
from app.core.logger import get_request_id


_DB_PATH = Path(settings.INGESTION_DB_PATH)


def _connect() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_ingestion_registry() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ingestion_jobs (
                resource_id TEXT NOT NULL,
                version TEXT NOT NULL,
                filename TEXT NOT NULL,
                course_id TEXT NOT NULL,
                chapter_id TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                pages_processed INTEGER,
                chunks_indexed INTEGER NOT NULL DEFAULT 0,
                message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (resource_id, version)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                success INTEGER NOT NULL,
                duration_ms INTEGER,
                request_id TEXT,
                provider TEXT,
                fallback_used INTEGER,
                resource_id TEXT,
                version TEXT,
                course_id TEXT,
                chapter_id TEXT,
                payload_hash TEXT,
                details_json TEXT,
                error TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(audit_events)").fetchall()
        }
        if "request_id" not in columns:
            conn.execute("ALTER TABLE audit_events ADD COLUMN request_id TEXT")


def get_ingestion_job(resource_id: str, version: str) -> Optional[dict[str, Any]]:
    init_ingestion_registry()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT resource_id, version, filename, course_id, chapter_id, content_hash,
                   status, pages_processed, chunks_indexed, message, created_at, updated_at
            FROM ingestion_jobs
            WHERE resource_id = ? AND version = ?
            """,
            (resource_id, version),
        ).fetchone()

    return dict(row) if row else None


def upsert_ingestion_job(
    *,
    resource_id: str,
    version: str,
    filename: str,
    course_id: str,
    chapter_id: str,
    content_hash: str,
    status: str,
    pages_processed: Optional[int],
    chunks_indexed: int,
    message: Optional[str],
) -> dict[str, Any]:
    init_ingestion_registry()
    now = _now_iso()

    existing = get_ingestion_job(resource_id, version)
    created_at = existing["created_at"] if existing else now

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO ingestion_jobs (
                resource_id, version, filename, course_id, chapter_id, content_hash,
                status, pages_processed, chunks_indexed, message, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(resource_id, version)
            DO UPDATE SET
                filename = excluded.filename,
                course_id = excluded.course_id,
                chapter_id = excluded.chapter_id,
                content_hash = excluded.content_hash,
                status = excluded.status,
                pages_processed = excluded.pages_processed,
                chunks_indexed = excluded.chunks_indexed,
                message = excluded.message,
                updated_at = excluded.updated_at
            """,
            (
                resource_id,
                version,
                filename,
                course_id,
                chapter_id,
                content_hash,
                status,
                pages_processed,
                chunks_indexed,
                message,
                created_at,
                now,
            ),
        )

    saved = get_ingestion_job(resource_id, version)
    return saved or {}


def record_audit_event(
    *,
    event_type: str,
    endpoint: str,
    status_code: int,
    success: bool,
    duration_ms: Optional[int] = None,
    request_id: Optional[str] = None,
    provider: Optional[str] = None,
    fallback_used: Optional[bool] = None,
    resource_id: Optional[str] = None,
    version: Optional[str] = None,
    course_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    payload_hash: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    """Persist one audit trail event in SQLite. Never raises to callers."""
    try:
        init_ingestion_registry()
        resolved_request_id = request_id or get_request_id()
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_events (
                    event_type,
                    endpoint,
                    status_code,
                    success,
                    duration_ms,
                    request_id,
                    provider,
                    fallback_used,
                    resource_id,
                    version,
                    course_id,
                    chapter_id,
                    payload_hash,
                    details_json,
                    error,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_type,
                    endpoint,
                    status_code,
                    1 if success else 0,
                    duration_ms,
                    resolved_request_id,
                    provider,
                    None if fallback_used is None else (1 if fallback_used else 0),
                    resource_id,
                    version,
                    course_id,
                    chapter_id,
                    payload_hash,
                    json.dumps(details, ensure_ascii=False) if details else None,
                    error,
                    _now_iso(),
                ),
            )
    except Exception:
        return
