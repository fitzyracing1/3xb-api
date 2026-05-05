"""
Database connection — PostgreSQL (DATABASE_URL) in production, SQLite locally.
"""

import os
import sqlite3
from contextlib import contextmanager

DATABASE_URL = os.environ.get("DATABASE_URL")
SQLITE_PATH  = os.environ.get("DB_PATH", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "3xb_internet.db"
))

USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras


def _pg_sql(sql: str) -> str:
    """Convert SQLite-style ? placeholders to Postgres %s."""
    return sql.replace("?", "%s")


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
    """Run a SELECT, return list of dicts (or one dict if one=True)."""
    with get_conn() as conn:
        if USE_POSTGRES:
            cur = conn.cursor()
            cur.execute(_pg_sql(sql), params)
            rows = [dict(r) for r in cur.fetchall()]
        else:
            rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    return rows[0] if (one and rows) else rows


def execute(sql: str, params: tuple = ()):
    """Run INSERT / UPDATE / DELETE."""
    with get_conn() as conn:
        if USE_POSTGRES:
            cur = conn.cursor()
            cur.execute(_pg_sql(sql), params)
            conn.commit()
        else:
            conn.execute(sql, params)
            conn.commit()
