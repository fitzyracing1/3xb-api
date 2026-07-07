# 3XB Entity Graph API

**3XB is a web entity intelligence service: it serves a weighted graph of people, organizations, and locations extracted from across the web — scored by prominence, linked by co-occurrence, and decayed over time — through a REST API whose flagship product is an APPROVE / REVIEW / DECLINE loan score for thin-file borrowers.** Built by Community Plan, Inc. for CDFIs and community lenders, alternative-data buyers, and NLP researchers.

The graph itself is produced by a separate crawler (the `mars-crawler` project); this repository is the API layer that serves it, plus the deployment config (Railway), landing page (GitHub Pages), and Stripe subscription billing.

## How it works

Every entity in the graph has:

- **Prominence weight** (0–1) — how frequently and prominently it appears across the web
- **Temporal decay** — weights halve every 30 days without fresh mentions, keeping scores current
- **Relationship edges** — entities that appear on the same page are linked with a strength score
- **Loan score** — a composite of the borrower's own decayed weight (70%) and the average decayed, strength-weighted score of its graph neighbors (30%), mapped to a verdict:
  - `composite >= 0.75` → **APPROVE**
  - `composite >= 0.55` → **REVIEW**
  - otherwise → **DECLINE**

## Install and run

Requires Python 3.10+.

```bash
git clone https://github.com/fitzyracing1/3xb-api.git
cd 3xb-api
pip install -r requirements.txt

# Populate a local SQLite database with sample graph data
python3 seed.py

# Start the API (http://localhost:8000, interactive docs at /docs)
python3 api.py
```

The database schema is created automatically on startup. With no configuration the API uses a local SQLite file (`3xb_internet.db`); in production it uses PostgreSQL.

### Configuration

All configuration is via environment variables — none are required for local development:

| Variable | Purpose |
|---|---|
| `PG_URL` or `DATABASE_URL` | PostgreSQL connection string. If unset, SQLite is used. |
| `DB_PATH` | Path to the SQLite file (default: `3xb_internet.db` next to the code). |
| `PORT` | HTTP port (default `8000`). |
| `STRIPE_SECRET_KEY` | Stripe API key. Checkout endpoints return 503 until set. |
| `STRIPE_STARTER_PRICE_ID`, `STRIPE_GROWTH_PRICE_ID` | Stripe price IDs for the two subscription plans. |
| `STRIPE_WEBHOOK_SECRET` | Verifies `/webhook` signatures when set. |

## API endpoints

Interactive documentation lives at `/docs` (Swagger UI).

| Endpoint | Description |
|---|---|
| `GET /stats` | Live crawl stats: page, entity, and edge counts, breakdown by type, top 5 entities |
| `GET /entities?tag=Person&min_weight=0.7&sort_by=weight&limit=50` | Filtered, sorted entity list |
| `GET /entity/{name}` | Full profile: tag, raw and live (decayed) weight, frequency, neighbors. Name matching is case-insensitive. |
| `GET /entity/{name}/loan-score` | APPROVE / REVIEW / DECLINE verdict with composite score and neighbor risk |
| `GET /search?q=goog` | Case-insensitive substring search |
| `GET /tag/{tag}` and `GET /tags` | Entities by type; list of all types with counts |
| `GET /graph?top_n=200&min_weight=0.5` | Node + edge graph as JSON (powers the D3 visualization) |
| `GET /export?tag=Person&include_loan_score=true` | CSV download, optionally with loan verdicts |
| `POST /entity/{name}/signal?signal_strength=0.8` | Inject a real-time signal (e.g. X engagement) to boost an entity's weight |
| `POST /checkout/{plan}` | Start a Stripe subscription checkout (`starter` or `growth`) |
| `POST /webhook` | Stripe webhook receiver |
| `GET /health` | Health check (used by Railway) |

### Example

```bash
curl http://localhost:8000/entity/Google/loan-score
```

```json
{
  "borrower": "Google",
  "own_weight": 0.7293,
  "neighbor_risk_avg": 0.6147,
  "composite_score": 0.6949,
  "recommendation": "REVIEW",
  "neighbor_count": 4
}
```

## Tests

```bash
pip install -r requirements-dev.txt
python3 -m pytest
```

The suite runs the full app against a temporary SQLite database and covers every endpoint: stats, entity lookup (including case-insensitive fallback and 404s), loan scoring math, search, tags, graph (including the empty-result edge case), CSV export with and without loan scores, signal injection and its weight cap, checkout degradation without Stripe, and the temporal-decay function.

## Deployment

- **API** — deploys to [Railway](https://railway.app) using `railway.json` / `Procfile` (`uvicorn api:app`). Set `PG_URL` to your PostgreSQL instance. A `/health` endpoint is configured as the healthcheck.
- **Landing page** — `index.html` is served via GitHub Pages at the custom domain in `CNAME` (earthenwarecomputer.com).
- **Data migration** — `migrate.py` pushes a local SQLite crawl database into PostgreSQL: `DATABASE_URL=<pg-url> python3 migrate.py` (set `SQLITE_PATH` to point at the crawler's database).

## Repository layout

| File | Purpose |
|---|---|
| `api.py` | FastAPI application — all routes |
| `db.py` | Database layer: schema, PostgreSQL/SQLite dual backend |
| `seed.py` | Sample-data seeder for local development |
| `migrate.py` | SQLite → PostgreSQL migration for production data |
| `tests/` | Pytest suite |
| `index.html`, `CNAME`, `robots.txt`, `sitemap.xml`, `llms.txt` | Landing page, SEO, and AI-discoverability files |
| `pitches.md`, `producthunt.md` | Sales and launch copy |
| `railway.json`, `Procfile` | Deployment config |

## Contact

Community Plan, Inc. — almeidacorporation20@gmail.com — https://earthenwarecomputer.com
