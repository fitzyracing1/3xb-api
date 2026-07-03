# 3XB Entity Graph API

A REST API (Python / [FastAPI](https://fastapi.tiangolo.com/)) that serves a weighted
entity graph — entities, relationship edges, and crawled pages — with endpoints for
search, stats, CSV export, graph extraction, and a composite "loan score" per entity.
It uses SQLite for local development and PostgreSQL in production (set via
`DATABASE_URL` or `PG_URL`). Stripe checkout endpoints are included but optional.

The repository also contains a static GitHub Pages landing site (`index.html`,
`CNAME`, `sitemap.xml`, etc.) and deployment config for Railway
(`railway.json`, `Procfile`).

## Requirements

- Python 3.12+ (tested with 3.12.3)

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

(On Debian/Ubuntu, if venv creation fails, first run
`sudo apt-get install python3.12-venv`.)

## Run

```bash
.venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000
```

Or, with auto-reload for development:

```bash
.venv/bin/python api.py
```

On first start with no database configured, the app creates an empty SQLite
database at `3xb_internet.db` (override the path with `DB_PATH`). To run
against PostgreSQL instead, set `DATABASE_URL` (or `PG_URL`) to a
`postgres://...` connection string.

## Verify

```bash
curl http://localhost:8000/health
# {"status":"ok"}

curl http://localhost:8000/stats
# {"pages_crawled":0,"unique_entities":0,"relationship_edges":0,...}
```

Interactive API docs are served at [http://localhost:8000/docs](http://localhost:8000/docs).

## Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Health check |
| `GET /stats` | Counts and top entities |
| `GET /entities` | List entities (`limit`, `min_weight`, `tag`, `sort_by`) |
| `GET /entity/{name}` | Single entity with decayed live weight and neighbors |
| `GET /entity/{name}/loan-score` | Composite score from own weight + neighbor weights |
| `GET /search?q=` | Substring search on entity names |
| `GET /tag/{tag}` / `GET /tags` | Entities by tag / tag summary |
| `GET /export` | CSV export (`tag`, `min_weight`, `include_loan_score`) |
| `GET /graph` | Top-N nodes and the edges between them |
| `POST /entity/{name}/signal` | Boost an entity's weight from an external signal |
| `POST /checkout/{plan}` | Stripe checkout (requires `STRIPE_SECRET_KEY` and price IDs) |

## Environment variables (all optional for local dev)

| Variable | Purpose |
|---|---|
| `PORT` | Server port for `python api.py` (default 8000) |
| `DATABASE_URL` / `PG_URL` | PostgreSQL connection string; falls back to SQLite if unset |
| `DB_PATH` | SQLite file path (default `./3xb_internet.db`) |
| `STRIPE_SECRET_KEY`, `STRIPE_STARTER_PRICE_ID`, `STRIPE_GROWTH_PRICE_ID`, `STRIPE_WEBHOOK_SECRET` | Stripe billing endpoints |

## Migrating local data to PostgreSQL

`migrate.py` copies an existing local SQLite database into PostgreSQL:

```bash
SQLITE_PATH=./3xb_internet.db DATABASE_URL=postgres://... .venv/bin/python migrate.py
```
