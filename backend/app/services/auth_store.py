"""SQLite storage for user accounts and auth tokens.

Separate file (auth.sqlite3) from the knowledge base store; same data dir,
same WAL/atomicity guarantees. Tokens are stored as SHA-256 hashes — a DB
leak never leaks usable bearer tokens.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Iterator, Optional

from app.config import settings

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email         TEXT NOT NULL DEFAULT '',
    role          TEXT NOT NULL DEFAULT 'user',
    disabled      INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tokens (
    token_hash TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tokens_user ON tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_tokens_expire ON tokens(expires_at);
"""

_init_lock = threading.Lock()
_initialized = False


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    global _initialized
    path = settings.data_dir / "auth.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
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


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def get_user_by_username(username: str) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, email, role, disabled FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row is None:
        return None
    return {"id": row[0], "username": row[1], "passwordHash": row[2], "email": row[3], "role": row[4], "disabled": bool(row[5])}


def get_user_by_id(user_id: int) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, username, email, role, disabled FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if row is None:
        return None
    return {"id": row[0], "username": row[1], "email": row[2], "role": row[3], "disabled": bool(row[4])}


def username_exists(username: str) -> bool:
    with _connect() as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,)).fetchone()
    return count > 0


def create_user(username: str, password_hash: str, email: str = "", role: str = "user") -> dict:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO users(username, password_hash, email, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, email.strip(), role, _now()),
        )
    return get_user_by_id(cur.lastrowid)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_token(user_id: int) -> tuple[str, str]:
    """Create a token; returns (plaintext_token, expires_at_iso)."""
    token = secrets.token_urlsafe(32)
    expires = (datetime.now(timezone.utc) + timedelta(days=settings.token_ttl_days)).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO tokens(token_hash, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (hash_token(token), user_id, expires, _now()),
        )
    return token, expires


def resolve_token(token: str) -> Optional[dict]:
    """Return {user, token_hash, expires_at} for a valid, unexpired token."""
    row = None
    with _connect() as conn:
        row = conn.execute(
            "SELECT t.expires_at, u.id, u.username, u.email, u.role, u.disabled"
            " FROM tokens t JOIN users u ON u.id = t.user_id WHERE t.token_hash = ?",
            (hash_token(token),),
        ).fetchone()
    if row is None:
        return None
    expires_at, user_id, username, email, role, disabled = row
    if disabled:
        return None
    try:
        expires_dt = datetime.fromisoformat(expires_at)
        if expires_dt <= datetime.now(timezone.utc):
            return None
    except ValueError:
        return None
    return {
        "tokenHash": hash_token(token),
        "expiresAt": expires_at,
        "user": {"id": user_id, "username": username, "email": email, "role": role},
    }


def touch_token(token_hash: str) -> None:
    """Sliding expiry: only rewrite when >1h since last update (avoid write amplification)."""
    new_expiry = (datetime.now(timezone.utc) + timedelta(days=settings.token_ttl_days)).isoformat()
    with _connect() as conn:
        conn.execute(
            "UPDATE tokens SET expires_at = ? WHERE token_hash = ?"
            " AND datetime(?) > datetime(expires_at, '-23 hours')",
            (new_expiry, token_hash, new_expiry),
        )


def revoke_token(token_hash: str) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM tokens WHERE token_hash = ?", (token_hash,))
    return cur.rowcount > 0


def purge_expired_tokens() -> int:
    """Housekeeping: drop expired tokens. Returns removed count."""
    now = _now()
    with _connect() as conn:
        cur = conn.execute("DELETE FROM tokens WHERE expires_at < ?", (now,))
    if cur.rowcount:
        logger.info("Purged %d expired auth tokens", cur.rowcount)
    return cur.rowcount
