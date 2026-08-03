"""
backend/core/db.py

PostgreSQL connection pool for AWS RDS.
Provides get_connection() for synchronous use (scripts, tasks)
and get_db_cursor() as a FastAPI dependency for async routes.
"""

from __future__ import annotations
import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool

# Load .env for local dev
try:
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

_pool: pool.ThreadedConnectionPool | None = None


def _get_pool() -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL environment variable is not set.")
        _pool = pool.ThreadedConnectionPool(1, 10, db_url)
    return _pool


@contextmanager
def get_connection():
    """Synchronous context manager — for scripts and Celery tasks."""
    p = _get_pool()
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def get_db_cursor():
    """
    FastAPI dependency — yields a RealDictCursor then commits/rolls back.
    Usage:
        @router.get("/something")
        async def endpoint(cursor=Depends(get_db_cursor)):
            cursor.execute("SELECT 1")
    """
    with get_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
        finally:
            cursor.close()
