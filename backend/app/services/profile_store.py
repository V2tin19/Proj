"""SQLite storage for per-user resume profiles.

First user-scoped business data in the app (resume snapshots the user can
save / switch between). Follows the kb_store storage pattern:
- separate ``profiles.sqlite3`` in settings.data_dir
- WAL journal, short-lived per-call connections, lazy schema init
- all queries scoped by ``user_id`` so profiles of different accounts on a
  shared server never mix

Schema:
    resume_profiles(id, user_id, name, remark, data JSON, created_at, updated_at)
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator, Optional

from app.config import settings

MAX_PROFILES_PER_USER = 50
MAX_DATA_JSON_BYTES = 512 * 1024  # 512KB,头像 base64 亦在此限内

_SCHEMA = """
CREATE TABLE IF NOT EXISTS resume_profiles (
    id         TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL,
    name       TEXT NOT NULL,
    remark     TEXT NOT NULL DEFAULT '',
    data       TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_resume_profiles_user ON resume_profiles(user_id);
"""

_init_lock = threading.Lock()
_initialized = False


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    global _initialized
    path = settings.profiles_db_path
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


def _check_data_size(data: dict[str, Any]) -> None:
    encoded = json.dumps(data, ensure_ascii=False).encode("utf-8")
    if len(encoded) > MAX_DATA_JSON_BYTES:
        raise ValueError("档案数据过大(超过 512KB),请精简内容或压缩头像后重试")


def _row_to_meta(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "remark": row["remark"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _row_to_profile(row: sqlite3.Row) -> dict[str, Any]:
    profile = _row_to_meta(row)
    profile["data"] = json.loads(row["data"])
    return profile


def list_profiles(user_id: int) -> list[dict[str, Any]]:
    """Metadata only (no snapshot payloads), most recently updated first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, name, remark, created_at, updated_at FROM resume_profiles"
            " WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    return [_row_to_meta(row) for row in rows]


def get_profile(user_id: int, profile_id: str) -> Optional[dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, name, remark, data, created_at, updated_at FROM resume_profiles"
            " WHERE user_id = ? AND id = ?",
            (user_id, profile_id),
        ).fetchone()
    return _row_to_profile(row) if row else None


def create_profile(user_id: int, name: str, remark: str, data: dict[str, Any]) -> dict[str, Any]:
    _check_data_size(data)
    with _connect() as conn:
        (count,) = conn.execute(
            "SELECT COUNT(*) FROM resume_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        if count >= MAX_PROFILES_PER_USER:
            raise ValueError(f"档案数量已达上限({MAX_PROFILES_PER_USER} 份),请先删除不需要的档案")

        now = _now()
        profile_id = f"prof-{uuid.uuid4().hex}"
        conn.execute(
            "INSERT INTO resume_profiles (id, user_id, name, remark, data, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (profile_id, user_id, name, remark, json.dumps(data, ensure_ascii=False), now, now),
        )
        row = conn.execute(
            "SELECT id, name, remark, data, created_at, updated_at FROM resume_profiles"
            " WHERE user_id = ? AND id = ?",
            (user_id, profile_id),
        ).fetchone()
    return _row_to_profile(row)


def update_profile(
    user_id: int,
    profile_id: str,
    *,
    name: Optional[str] = None,
    remark: Optional[str] = None,
    data: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    if data is not None:
        _check_data_size(data)

    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM resume_profiles WHERE user_id = ? AND id = ?",
            (user_id, profile_id),
        ).fetchone()
        if row is None:
            raise ValueError("Profile not found")

        assignments: list[str] = ["updated_at = ?"]
        values: list[Any] = [_now()]
        if name is not None:
            assignments.append("name = ?")
            values.append(name)
        if remark is not None:
            assignments.append("remark = ?")
            values.append(remark)
        if data is not None:
            assignments.append("data = ?")
            values.append(json.dumps(data, ensure_ascii=False))
        values.extend([profile_id, user_id])

        conn.execute(
            f"UPDATE resume_profiles SET {', '.join(assignments)} WHERE id = ? AND user_id = ?",
            values,
        )
        updated = conn.execute(
            "SELECT id, name, remark, data, created_at, updated_at FROM resume_profiles"
            " WHERE user_id = ? AND id = ?",
            (user_id, profile_id),
        ).fetchone()
    return _row_to_profile(updated)


def delete_profile(user_id: int, profile_id: str) -> bool:
    with _connect() as conn:
        cursor = conn.execute(
            "DELETE FROM resume_profiles WHERE user_id = ? AND id = ?",
            (user_id, profile_id),
        )
    return cursor.rowcount > 0
