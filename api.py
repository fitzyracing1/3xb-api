"""
3XB Entity Graph API
REST interface into the live 3XB entity database.
Supports PostgreSQL (production) and SQLite (local dev).
"""

import math
import os
import time
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import stripe

import db

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")

PLANS = {
    "starter": {
        "price_id": os.environ.get("STRIPE_STARTER_PRICE_ID", ""),
        "name": "3XB Starter — $500/mo",
    },
    "growth": {
        "price_id": os.environ.get("STRIPE_GROWTH_PRICE_ID", ""),
        "name": "3XB Growth — $1,500/mo",
    },
}

PORT = int(os.environ.get("PORT", 8000))

app = FastAPI(
    title="3XB Entity Graph API",
    description="Weighted entity tagging across the web — by Community Plan, Inc.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def decay_weight(weight: float, last_seen: float, half_life_days: float = 30.0) -> float:
    days = (time.time() - last_seen) / 86400
    factor = math.exp(-math.log(2) * days / half_life_days)
    return round(weight * factor, 4)


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.get("/health", include_in_schema=False)
def health():
    return JSONResponse({"status": "ok"})


@app.get("/debug", include_in_schema=False)
def debug():
    pg_url  = os.environ.get("PG_URL", "")
    db_url  = os.environ.get("DATABASE_URL", "")
    active  = pg_url or db_url
    masked  = active[:35] + "..." if len(active) > 35 else active
    return JSONResponse({
        "PG_URL": pg_url[:20] + "..." if pg_url else "NOT SET",
        "DATABASE_URL": db_url[:20] + "..." if db_url else "NOT SET",
        "USE_POSTGRES": db.USE_POSTGRES,
        "active_url": masked,
    })


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    return """
    <html><head><title>3XB API</title>
    <style>body{font-family:monospace;background:#0a0a0f;color:#7df7ff;padding:40px}
    a{color:#ff6b9d} h1{color:#fff} li{margin:6px 0}</style></head>
    <body>
    <h1>3XB Entity Graph API v2.0</h1>
    <p>Weighted entity tagging across the web — Community Plan, Inc.</p>
    <ul>
      <li><a href="/docs">Interactive API Docs</a></li>
      <li><a href="/stats">GET /stats</a></li>
      <li><a href="/entities?limit=20">GET /entities</a></li>
      <li>GET /entity/{name}</li>
      <li>GET /entity/{name}/loan-score</li>
      <li>GET /search?q=</li>
      <li>GET /graph</li>
    </ul>
    </body></html>
    """


@app.get("/stats")
def stats():
    pages    = db.query("SELECT COUNT(*) as n FROM crawled_urls", one=True)["n"]
    entities = db.query("SELECT COUNT(*) as n FROM entities", one=True)["n"]
    edges    = db.query("SELECT COUNT(*) as n FROM edges", one=True)["n"]
    tags     = db.query("SELECT tag, COUNT(*) as n FROM entities GROUP BY tag ORDER BY n DESC")
    top5     = db.query("SELECT name, tag, weight, frequency FROM entities ORDER BY weight DESC, frequency DESC LIMIT 5")
    return {
        "pages_crawled": pages,
        "unique_entities": entities,
        "relationship_edges": edges,
        "entities_by_type": {r["tag"]: r["n"] for r in tags},
        "top_5": top5,
    }


@app.get("/entities")
def list_entities(
    limit: int = Query(50, le=500),
    min_weight: float = Query(0.0, ge=0.0, le=1.0),
    tag: Optional[str] = None,
    sort_by: str = Query("weight", enum=["weight", "frequency"]),
):
    order = "weight DESC, frequency DESC" if sort_by == "weight" else "frequency DESC, weight DESC"
    if tag:
        return db.query(
            f"SELECT name, tag, weight, frequency FROM entities WHERE tag=? AND weight>=? ORDER BY {order} LIMIT ?",
            (tag, min_weight, limit)
        )
    return db.query(
        f"SELECT name, tag, weight, frequency FROM entities WHERE weight>=? ORDER BY {order} LIMIT ?",
        (min_weight, limit)
    )


@app.get("/entity/{name}")
def get_entity(name: str):
    row = db.query("SELECT * FROM entities WHERE name=?", (name,), one=True)
    if not row:
        raise HTTPException(404, f"Entity '{name}' not found")
    row["live_weight"] = decay_weight(row["weight"], row["last_seen"])
    row["highlighted"] = row["live_weight"] >= 0.75
    row["neighbors"] = db.query(
        "SELECT target as entity, relation, strength FROM edges WHERE source=? LIMIT 50",
        (name,)
    )
    return row


@app.get("/entity/{name}/loan-score")
def loan_score(name: str):
    row = db.query("SELECT weight, last_seen FROM entities WHERE name=?", (name,), one=True)
    if not row:
        raise HTTPException(404, f"Entity '{name}' not found")
    own_weight = decay_weight(row["weight"], row["last_seen"])
    edges = db.query("SELECT target, strength FROM edges WHERE source=?", (name,))
    neighbor_scores = []
    for e in edges:
        nb = db.query("SELECT weight, last_seen FROM entities WHERE name=?", (e["target"],), one=True)
        if nb:
            neighbor_scores.append(decay_weight(nb["weight"], nb["last_seen"]) * e["strength"])
    neighbor_avg = round(sum(neighbor_scores) / len(neighbor_scores), 4) if neighbor_scores else own_weight
    composite = round(own_weight * 0.7 + neighbor_avg * 0.3, 4)
    return {
        "borrower": name,
        "own_weight": own_weight,
        "neighbor_risk_avg": neighbor_avg,
        "composite_score": composite,
        "recommendation": "APPROVE" if composite >= 0.75 else "REVIEW" if composite >= 0.55 else "DECLINE",
        "neighbor_count": len(neighbor_scores),
    }


@app.get("/search")
def search(q: str = Query(..., min_length=2), limit: int = Query(20, le=100)):
    return db.query(
        "SELECT name, tag, weight, frequency FROM entities WHERE name LIKE ? ORDER BY weight DESC LIMIT ?",
        (f"%{q}%", limit)
    )


@app.get("/tag/{tag}")
def by_tag(tag: str, limit: int = Query(50, le=200)):
    rows = db.query(
        "SELECT name, tag, weight, frequency FROM entities WHERE tag=? ORDER BY weight DESC LIMIT ?",
        (tag, limit)
    )
    if not rows:
        raise HTTPException(404, f"No entities for tag '{tag}'")
    return rows


@app.get("/tags")
def list_tags():
    return db.query("SELECT tag, COUNT(*) as count, AVG(weight) as avg_weight FROM entities GROUP BY tag ORDER BY count DESC")


@app.get("/graph")
def graph(
    top_n: int = Query(200, le=1000),
    min_weight: float = Query(0.5, ge=0.0, le=1.0),
):
    nodes = db.query(
        "SELECT name, tag, weight, frequency FROM entities WHERE weight>=? ORDER BY weight DESC, frequency DESC LIMIT ?",
        (min_weight, top_n)
    )
    node_ids = {n["name"] for n in nodes}
    all_edges = db.query("SELECT source, target, relation, strength FROM edges LIMIT 5000")
    edges = [e for e in all_edges if e["source"] in node_ids and e["target"] in node_ids][:2000]
    return {"nodes": nodes, "edges": edges, "meta": {"node_count": len(nodes), "edge_count": len(edges)}}


@app.post("/entity/{name}/signal")
def inject_signal(name: str, signal_strength: float = Query(..., ge=0.0, le=1.0), signal_type: str = "x_engagement"):
    row = db.query("SELECT weight FROM entities WHERE name=?", (name,), one=True)
    if not row:
        raise HTTPException(404, f"Entity '{name}' not found")
    new_weight = min(0.9999, round(row["weight"] + signal_strength * 0.1, 4))
    db.execute("UPDATE entities SET weight=?, last_seen=? WHERE name=?", (new_weight, time.time(), name))
    return {"entity": name, "signal_type": signal_type, "weight_before": row["weight"], "weight_after": new_weight}


@app.post("/checkout/{plan}")
def create_checkout(plan: str, request: Request):
    if not stripe.api_key:
        raise HTTPException(503, "Stripe not configured")
    plan_data = PLANS.get(plan)
    if not plan_data:
        raise HTTPException(404, f"Unknown plan '{plan}'")
    if not plan_data["price_id"]:
        raise HTTPException(503, f"Price ID for '{plan}' not configured")
    origin = str(request.base_url).rstrip("/")
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": plan_data["price_id"], "quantity": 1}],
        success_url=f"{origin}/?checkout=success",
        cancel_url=f"{origin}/?checkout=cancel",
    )
    return {"url": session.url}


@app.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    if secret:
        try:
            event = stripe.Webhook.construct_event(payload, sig, secret)
        except Exception:
            raise HTTPException(400, "Invalid signature")
    else:
        import json
        event = json.loads(payload)
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print(f"[stripe] new subscription: {session.get('customer_email')} — {session.get('id')}")
    return {"received": True}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=PORT, reload=True)
