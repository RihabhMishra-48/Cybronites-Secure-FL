"""
Thread-safe SQLite database manager with WAL mode and auto-migration.
"""
from __future__ import annotations

import sqlite3
import threading
import json
import logging
from pathlib import Path
from contextlib import contextmanager

from secure_training_platform.config import DATABASE_PATH
from secure_training_platform.database.schema import SCHEMA_SQL

logger = logging.getLogger(__name__)

_local = threading.local()
_init_lock = threading.Lock()
_initialized = False


def _get_connection() -> sqlite3.Connection:
    """Get a thread-local SQLite connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(
            str(DATABASE_PATH),
            check_same_thread=False,
            timeout=30.0
        )
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
        _local.conn.execute("PRAGMA busy_timeout=5000")
    return _local.conn


def init_db():
    """Initialize database schema (idempotent)."""
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        conn = _get_connection()
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        _initialized = True
        logger.info(f"Database initialized at {DATABASE_PATH}")


@contextmanager
def get_db():
    """Context manager yielding a database connection."""
    init_db()
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def execute_query(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a SELECT query and return list of dicts."""
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def execute_insert(sql: str, params: tuple = ()) -> str | None:
    """Execute an INSERT/UPDATE and return lastrowid."""
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid


def execute_many(sql: str, params_list: list[tuple]):
    """Execute a batch of statements."""
    with get_db() as conn:
        conn.executemany(sql, params_list)
        conn.commit()
