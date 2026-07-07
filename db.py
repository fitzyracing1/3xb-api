"""
Database connection — PostgreSQL (DATABASE_URL) in production, SQLite locally.
"""

import os
import sqlite3
from contextlib import contextmanager

DATABASE_URL = os.environ.get("PG_URL") or os.environ.get("DATABASE_URL") or ""
SQLITE_PATH  = os.environ.get("DB_PATH", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "3xb_internet.db"
))

USE_POSTGRES = DATABASE_URL.startswith("postgres")

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras


class DatabaseError(Exception):
    """Raised when the underlying database cannot be reached or a query fails."""


SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS entities (
        name TEXT PRIMARY KEY,
        tag TEXT,
        weight REAL,
        frequency INTEGER DEFAULT 1,
        last_seen REAL,
        metadata TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS edges (
        source TEXT,
        target TEXT,
        relation TEXT,
        strength REAL,
        PRIMARY KEY (source, target, relation)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS crawled_urls (
        url TEXT PRIMARY KEY,
        crawled_at REAL,
        entity_count INTEGER
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_entities_weight ON entities (weight DESC)",
    "CREATE INDEX IF NOT EXISTS idx_entities_tag ON entities (tag)",
    "CREATE INDEX IF NOT EXISTS idx_edges_source ON edges (source)",
]


def _pg_sql(sql: str) -> str:
    """Convert SQLite-style ? placeholders to Postgres %s."""
    return sql.replace("?", "%s")


def init_db():
    """Create tables and indexes if they don't exist (idempotent)."""
    with get_conn() as conn:
        cur = conn.cursor() if USE_POSTGRES else conn
        for stmt in SCHEMA:
            cur.execute(stmt)
        conn.commit()


@contextmanager
def get_conn():
    if USE_POSTGRES:
        conn = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=psycopg2.extras.RealDictCursor,
            sslmode="require",
        )
        try:
            yield conn
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


def query(sql: str, params: tuple = (), one: bool = False):
    """Run a SELECT, return list of dicts (or one dict / None if one=True)."""
    try:
        with get_conn() as conn:
            if USE_POSTGRES:
                cur = conn.cursor()
                cur.execute(_pg_sql(sql), params)
                rows = [dict(r) for r in cur.fetchall()]
            else:
                rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    except (sqlite3.Error,) + ((psycopg2.Error,) if USE_POSTGRES else ()) as e:
        raise DatabaseError(str(e)) from e
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql: str, params: tuple = ()):
    """Run INSERT / UPDATE / DELETE."""
    try:
        with get_conn() as conn:
            if USE_POSTGRES:
                cur = conn.cursor()
                cur.execute(_pg_sql(sql), params)
                conn.commit()
            else:
                conn.execute(sql, params)
                conn.commit()
    except (sqlite3.Error,) + ((psycopg2.Error,) if USE_POSTGRES else ()) as e:
        raise DatabaseError(str(e)) from e
