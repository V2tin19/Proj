"""Usage/audit event storage (single append-only table).

Every meaningful action is recorded here once: business usage (generate /
chat / export), account lifecycle (register / login / password reset /
disable) and operator actions (llm config). The admin console reads
aggregates (stats) and the raw log (audit) from this one table.

Schema:
    events(id, at, user_id, username, type, detail)
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Iterator, Optional

from app.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    at       TEXT NOT NULL,
    user_id  INTEGER,
    username TEXT NOT NULL DEFAULT '',
    type     TEXT NOT NULL,
    detail   TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_events_at ON events(at);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
"""

_init_lock = threading.Lock()
_initialized = False


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    global _initialized
    path = settings.data_dir / "usage.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        if not _initialized:
            with _init_lock:
                if not _initialized:
                    conn.executescript(_SCHEMA)
                    _initialized = True
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(_SCHEMA)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_event(user: Optional[dict], event_type: str, detail: str = "") -> None:
    """Append one event. Never raises (audit must not break business flow)."""
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO events(at, user_id, username, type, detail) VALUES (?, ?, ?, ?, ?)",
                (
                    _now(),
                    (user or {}).get("id"),
                    (user or {}).get("username", "") or "anonymous",
                    event_type,
                    detail,
                ),
            )
    except Exception:  # pragma: no cover - 审计失败仅记日志
        import logging

        logging.getLogger(__name__).warning("record_event failed: %s", event_type)


def list_events(limit: int = 200, offset: int = 0, event_type: str = "") -> list[dict]:
    with _connect() as conn:
        if event_type:
            rows = conn.execute(
                "SELECT id, at, user_id, username, type, detail FROM events"
                " WHERE type = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                (event_type, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, at, user_id, username, type, detail FROM events"
                " ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
    return [
        {
            "id": row["id"], "at": row["at"], "userId": row["user_id"],
            "username": row["username"], "type": row["type"], "detail": row["detail"],
        }
        for row in rows
    ]


def _since(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def stats() -> dict:
    """Aggregates for the admin overview page."""
    with _connect() as conn:
        totals: dict[str, int] = {
            row["type"]: row["n"]
            for row in conn.execute(
                "SELECT type, COUNT(*) AS n FROM events WHERE at >= ? GROUP BY type",
                (_since(30),),
            ).fetchall()
        }

        # 生成来源占比(近30天,detail 记录 provider)
        providers = {
            row["detail"]: row["n"]
            for row in conn.execute(
                "SELECT detail, COUNT(*) AS n FROM events"
                " WHERE type = 'generate' AND at >= ? GROUP BY detail",
                (_since(30),),
            ).fetchall()
        }

        # 近14天逐日生成量
        daily = [
            {"day": row["day"], "count": row["n"]}
            for row in conn.execute(
                "SELECT substr(at, 1, 10) AS day, COUNT(*) AS n FROM events"
                " WHERE type = 'generate' AND at >= ? GROUP BY day ORDER BY day",
                (_since(14),),
            ).fetchall()
        ]

        # 近30天活跃用户(按事件数)
        top_users = [
            {"username": row["username"], "events": row["n"]}
            for row in conn.execute(
                "SELECT username, COUNT(*) AS n FROM events"
                " WHERE at >= ? AND username != 'anonymous' GROUP BY username"
                " ORDER BY n DESC LIMIT 10",
                (_since(30),),
            ).fetchall()
        ]

    return {
        "last30Days": totals,
        "generateProviders": providers,
        "generateDaily14d": daily,
        "topUsers": top_users,
    }
