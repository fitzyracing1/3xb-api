"""
End-to-end tests for the 3XB Entity Graph API against a temporary SQLite database.

Run with: python3 -m pytest
"""

import os
import sys
import tempfile
import time

import pytest
from fastapi.testclient import TestClient

# Point the app at a throwaway SQLite file before db.py reads the env
_tmpdir = tempfile.mkdtemp(prefix="3xb_test_")
os.environ["DB_PATH"] = os.path.join(_tmpdir, "test.db")
os.environ.pop("PG_URL", None)
os.environ.pop("DATABASE_URL", None)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db      # noqa: E402
import api     # noqa: E402


NOW = time.time()


@pytest.fixture(scope="session")
def client():
    db.init_db()
    db.execute(
        "INSERT INTO entities (name, tag, weight, frequency, last_seen, metadata) VALUES (?, ?, ?, ?, ?, ?)",
        ("Google", "Organization", 0.95, 1200, NOW, "{}"),
    )
    db.execute(
        "INSERT INTO entities (name, tag, weight, frequency, last_seen, metadata) VALUES (?, ?, ?, ?, ?, ?)",
        ("Sundar Pichai", "Person", 0.88, 800, NOW - 5 * 86400, "{}"),
    )
    db.execute(
        "INSERT INTO entities (name, tag, weight, frequency, last_seen, metadata) VALUES (?, ?, ?, ?, ?, ?)",
        ("Obscure Startup", "Organization", 0.12, 3, NOW - 90 * 86400, "{}"),
    )
    db.execute(
        "INSERT INTO edges (source, target, relation, strength) VALUES (?, ?, ?, ?)",
        ("Google", "Sundar Pichai", "led_by", 0.9),
    )
    db.execute(
        "INSERT INTO edges (source, target, relation, strength) VALUES (?, ?, ?, ?)",
        ("Sundar Pichai", "Google", "leads", 0.9),
    )
    db.execute(
        "INSERT INTO crawled_urls (url, crawled_at, entity_count) VALUES (?, ?, ?)",
        ("https://example.com/page1", NOW, 3),
    )
    with TestClient(api.app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_root_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "3XB Entity Graph API" in r.text


def test_stats(client):
    r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["pages_crawled"] == 1
    assert body["unique_entities"] == 3
    assert body["relationship_edges"] == 2
    assert body["entities_by_type"]["Organization"] == 2
    assert len(body["top_5"]) == 3
    assert body["top_5"][0]["name"] == "Google"


def test_list_entities(client):
    r = client.get("/entities?limit=10")
    assert r.status_code == 200
    rows = r.json()
    assert [e["name"] for e in rows[:2]] == ["Google", "Sundar Pichai"]


def test_list_entities_filters(client):
    r = client.get("/entities?tag=Person&min_weight=0.5")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["name"] == "Sundar Pichai"


def test_get_entity(client):
    r = client.get("/entity/Google")
    assert r.status_code == 200
    body = r.json()
    assert body["tag"] == "Organization"
    assert 0 < body["live_weight"] <= 0.95
    assert body["highlighted"] is True
    assert body["neighbors"][0]["entity"] == "Sundar Pichai"


def test_get_entity_case_insensitive(client):
    r = client.get("/entity/google")
    assert r.status_code == 200
    assert r.json()["name"] == "Google"


def test_get_entity_404(client):
    r = client.get("/entity/DoesNotExist")
    assert r.status_code == 404


def test_loan_score(client):
    r = client.get("/entity/Google/loan-score")
    assert r.status_code == 200
    body = r.json()
    assert body["borrower"] == "Google"
    assert body["neighbor_count"] == 1
    assert body["recommendation"] == "APPROVE"
    # composite = own*0.7 + neighbor_avg*0.3
    expected = round(body["own_weight"] * 0.7 + body["neighbor_risk_avg"] * 0.3, 4)
    assert abs(body["composite_score"] - expected) < 0.001


def test_loan_score_decline(client):
    r = client.get("/entity/Obscure Startup/loan-score")
    assert r.status_code == 200
    body = r.json()
    assert body["recommendation"] == "DECLINE"
    assert body["neighbor_count"] == 0


def test_loan_score_404(client):
    r = client.get("/entity/Nobody/loan-score")
    assert r.status_code == 404


def test_search(client):
    r = client.get("/search?q=goog")
    assert r.status_code == 200
    assert r.json()[0]["name"] == "Google"


def test_search_min_length(client):
    r = client.get("/search?q=a")
    assert r.status_code == 422


def test_tag_endpoints(client):
    r = client.get("/tag/Person")
    assert r.status_code == 200
    assert r.json()[0]["name"] == "Sundar Pichai"

    r = client.get("/tag/NoSuchTag")
    assert r.status_code == 404

    r = client.get("/tags")
    assert r.status_code == 200
    tags = {t["tag"]: t["count"] for t in r.json()}
    assert tags == {"Organization": 2, "Person": 1}


def test_graph(client):
    r = client.get("/graph?min_weight=0.5")
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["node_count"] == 2
    assert body["meta"]["edge_count"] == 2


def test_graph_no_nodes(client):
    # Regression: empty node set used to build "IN ()" and crash with a SQL error
    r = client.get("/graph?min_weight=0.999")
    assert r.status_code == 200
    body = r.json()
    assert body["nodes"] == []
    assert body["edges"] == []


def test_export_csv(client):
    r = client.get("/export")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    lines = r.text.strip().splitlines()
    assert lines[0] == "name,tag,weight,frequency,last_seen_unix"
    assert len(lines) == 4  # header + 3 entities


def test_export_csv_with_loan_score(client):
    r = client.get("/export?include_loan_score=true")
    assert r.status_code == 200
    lines = r.text.strip().splitlines()
    assert "recommendation" in lines[0]
    assert any("APPROVE" in line for line in lines[1:])


def test_signal_injection(client):
    before = client.get("/entity/Google").json()["weight"]
    r = client.post("/entity/Google/signal?signal_strength=0.5")
    assert r.status_code == 200
    body = r.json()
    assert body["weight_after"] > body["weight_before"]
    assert body["weight_before"] == before

    r = client.post("/entity/Nobody/signal?signal_strength=0.5")
    assert r.status_code == 404


def test_signal_weight_capped(client):
    for _ in range(5):
        client.post("/entity/Google/signal?signal_strength=1.0")
    weight = client.get("/entity/Google").json()["weight"]
    assert weight <= 0.9999


def test_checkout_unconfigured(client):
    # No Stripe key set in tests: should degrade gracefully, not crash
    r = client.post("/checkout/starter")
    assert r.status_code == 503

    r = client.post("/checkout/nonexistent-plan")
    assert r.status_code in (404, 503)


def test_decay_weight_math():
    w = api.decay_weight(0.8, time.time())
    assert abs(w - 0.8) < 0.01
    # After one half-life (30 days), weight should halve
    w = api.decay_weight(0.8, time.time() - 30 * 86400)
    assert abs(w - 0.4) < 0.01


def test_decay_weight_handles_missing_values():
    assert api.decay_weight(None, time.time()) == 0.0
    assert api.decay_weight(0.8, None) == 0.8
    # A last_seen in the future must not inflate the weight
    assert api.decay_weight(0.8, time.time() + 86400) <= 0.8
