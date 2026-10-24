"""Runtime configuration storage (operator-managed, layered over .env).

Stores operator overrides in ``runtime.sqlite3`` and applies them onto the
``settings`` singleton in place. Because every LLM call site (resume
generator, chat SSE proxy, health check) reads ``settings.llm_*`` live, a
write here takes effect immediately without a restart.

Layering: runtime DB override > .env default. Clearing the override restores
the .env values.

Schema:
    config(key TEXT PRIMARY KEY, value TEXT)  -- JSON-encoded values
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from typing import Iterator, Optional

from app.config import settings

LLM_KEY = "llm"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

_init_lock = threading.Lock()
_initialized = False

# .env 加载的原始值,清除运行时覆盖时恢复用
_env_defaults: Optional[dict] = None


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    global _initialized
    path = settings.data_dir / "runtime.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0)
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


def _read_llm_override() -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT value FROM config WHERE key = ?", (LLM_KEY,)
        ).fetchone()
    if row is None:
        return None
    try:
        parsed = json.loads(row[0])
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _remember_env_defaults() -> None:
    global _env_defaults
    if _env_defaults is None:
        _env_defaults = {
            "apiUrl": settings.llm_api_url,
            "apiKey": settings.llm_api_key,
            "model": settings.llm_model,
        }


def _apply_to_settings(values: dict) -> None:
    _remember_env_defaults()
    if "apiUrl" in values:
        settings.llm_api_url = values["apiUrl"]
    if "apiKey" in values and values["apiKey"]:
        settings.llm_api_key = values["apiKey"]
    if "model" in values and values["model"]:
        settings.llm_model = values["model"]


def load_and_apply() -> bool:
    """Startup hook: apply DB override (if any) onto settings.

    Returns True when a runtime override was applied.
    """
    override = _read_llm_override()
    if override is None:
        return False
    _apply_to_settings(override)
    return True


def get_llm_config() -> dict:
    """Current runtime override (raw values, no masking — route layer masks)."""
    return _read_llm_override() or {}


def save_llm_config(api_url: str, api_key: str, model: str) -> dict:
    """Persist the override and apply it onto settings immediately.

    Empty api_key keeps the previously stored (or env) key.
    """
    current = _read_llm_override() or {}
    merged = {
        "apiUrl": api_url,
        "apiKey": api_key or current.get("apiKey") or (_env_defaults or {}).get("apiKey", ""),
        "model": model,
    }
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO config(key, value) VALUES (?, ?)",
            (LLM_KEY, json.dumps(merged, ensure_ascii=False)),
        )
    _apply_to_settings(merged)
    return merged


def clear_llm_config() -> dict:
    """Drop the override; restore .env values onto settings."""
    global _env_defaults
    with _connect() as conn:
        conn.execute("DELETE FROM config WHERE key = ?", (LLM_KEY,))
    _remember_env_defaults()
    restored = _env_defaults or {}
    if _env_defaults:
        settings.llm_api_url = _env_defaults.get("apiUrl", "")
        settings.llm_api_key = _env_defaults.get("apiKey", "")
        settings.llm_model = _env_defaults.get("model", "")
    return restored
