"""
migrate.py — push local SQLite data into Railway PostgreSQL
Usage: DATABASE_URL=<railway-url> python3 migrate.py
"""

import os, sqlite3, psycopg2, psycopg2.extras, json, time

SQLITE = os.environ.get("SQLITE_PATH", "../mars-crawler/3xb_internet.db")
PG_URL = os.environ["DATABASE_URL"]

print(f"Connecting to PostgreSQL...")
pg = psycopg2.connect(PG_URL)
cur = pg.cursor()

print("Creating tables...")
cur.execute("""
    CREATE TABLE IF NOT EXISTS entities (
        name TEXT PRIMARY KEY, tag TEXT, weight REAL,
        frequency INTEGER DEFAULT 1, last_seen REAL, metadata TEXT
    )
""")
cur.execute("""
    CREATE TABLE IF NOT EXISTS edges (
        source TEXT, target TEXT, relation TEXT, strength REAL,
        PRIMARY KEY (source, target, relation)
    )
""")
cur.execute("""
    CREATE TABLE IF NOT EXISTS crawled_urls (
        url TEXT PRIMARY KEY, crawled_at REAL, entity_count INTEGER
    )
""")
pg.commit()

sq = sqlite3.connect(SQLITE)
sq.row_factory = sqlite3.Row

print("Migrating entities...")
rows = sq.execute("SELECT * FROM entities").fetchall()
psycopg2.extras.execute_values(cur,
    "INSERT INTO entities (name,tag,weight,frequency,last_seen,metadata) VALUES %s ON CONFLICT DO NOTHING",
    [(r["name"],r["tag"],r["weight"],r["frequency"],r["last_seen"],r["metadata"]) for r in rows],
    page_size=1000
)
pg.commit()
print(f"  {len(rows):,} entities migrated")

print("Migrating edges...")
rows = sq.execute("SELECT * FROM edges").fetchall()
for i in range(0, len(rows), 5000):
    batch = rows[i:i+5000]
    psycopg2.extras.execute_values(cur,
        "INSERT INTO edges (source,target,relation,strength) VALUES %s ON CONFLICT DO NOTHING",
        [(r["source"],r["target"],r["relation"],r["strength"]) for r in batch],
        page_size=1000
    )
    pg.commit()
    print(f"  {min(i+5000, len(rows)):,}/{len(rows):,} edges")

print("Migrating crawled URLs...")
rows = sq.execute("SELECT * FROM crawled_urls").fetchall()
psycopg2.extras.execute_values(cur,
    "INSERT INTO crawled_urls (url,crawled_at,entity_count) VALUES %s ON CONFLICT DO NOTHING",
    [(r["url"],r["crawled_at"],r["entity_count"]) for r in rows],
    page_size=1000
)
pg.commit()
print(f"  {len(rows):,} URLs migrated")

print("\nDone! Migration complete.")
pg.close()
sq.close()
