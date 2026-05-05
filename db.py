"""
Database connection — uses PostgreSQL (DATABASE_URL) in production,
SQLite fallback for local dev.
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


def _init_postgres(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            name        TEXT PRIMARY KEY,
            tag         TEXT,
            weight      REAL,
            frequency   INTEGER DEFAULT 1,
            last_seen   REAL,
            metadata    TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            source      TEXT,
            target      TEXT,
            relation    TEXT,
            strength    REAL,
            PRIMARY KEY (source, target, relation)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crawled_urls (
            url          TEXT PRIMARY KEY,
            crawled_at   REAL,
            entity_count INTEGER
        )
    """)
    conn.commit()


@contextmanager
def get_conn():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
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
    """Run a SELECT and return list of dicts (or one dict)."""
    if USE_POSTGRES:
        # Convert SQLite ? placeholders to Postgres %s
        sql = sql.replace("?", "%s")
    with get_conn() as conn:
        if USE_POSTGRES:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            result = [dict(r) for r in rows]
        else:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
            result = [dict(r) for r in rows]
    return result[0] if (one and result) else result


def execute(sql: str, params: tuple = ()):
    """Run INSERT / UPDATE / DELETE."""
    if USE_POSTGRES:
        sql = sql.replace("?", "%s")
        sql = sql.replace("ON CONFLICT(name)", "ON CONFLICT (name)")
        sql = sql.replace("ON CONFLICT(url)", "ON CONFLICT (url)")
        sql = sql.replace("INSERT OR REPLACE", "INSERT")
        if "INSERT" in sql and "ON CONFLICT" not in sql:
            sql = sql.rstrip() + " ON CONFLICT DO NOTHING"
    with get_conn() as conn:
        if USE_POSTGRES:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
        else:
            conn.execute(sql, params)
            conn.commit()
