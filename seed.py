"""
seed.py — populate the local database with a sample slice of the 3XB entity graph.

Run this once after cloning so the API has data to serve locally:

    python3 seed.py

Works against SQLite by default (3xb_internet.db next to this file) or against
PostgreSQL when PG_URL / DATABASE_URL is set — same as api.py.
"""

import random
import time

import db

# (name, tag, weight, frequency) — a representative sample of the production graph
ENTITIES = [
    ("Google",                "Organization",       0.98, 4210),
    ("Apple",                 "Organization",       0.97, 3980),
    ("Microsoft",             "Organization",       0.96, 3720),
    ("Amazon",                "Organization",       0.95, 3510),
    ("Tesla",                 "Organization",       0.93, 2890),
    ("OpenAI",                "Organization",       0.92, 2650),
    ("SEC",                   "Organization",       0.90, 2400),
    ("Federal Reserve",       "Organization",       0.89, 2210),
    ("Goldman Sachs",         "Organization",       0.87, 1980),
    ("JPMorgan Chase",        "Organization",       0.86, 1870),
    ("Reuters",               "Organization",       0.85, 1760),
    ("Opportunity Finance Network", "Organization", 0.72, 640),
    ("CDFI Fund",             "Organization",       0.70, 590),
    ("Accion",                "Organization",       0.66, 470),
    ("Community Plan, Inc.",  "Organization",       0.55, 210),
    ("Elon Musk",             "Person",             0.96, 3650),
    ("Tim Cook",              "Person",             0.91, 2380),
    ("Sundar Pichai",         "Person",             0.90, 2290),
    ("Satya Nadella",         "Person",             0.89, 2170),
    ("Sam Altman",            "Person",             0.88, 2050),
    ("Jerome Powell",         "Person",             0.87, 1940),
    ("Warren Buffett",        "Person",             0.86, 1820),
    ("Janet Yellen",          "Person",             0.84, 1650),
    ("Jane Fraser",           "Person",             0.78, 980),
    ("Joshua Fitzgerald",     "Person",             0.52, 140),
    ("United States",         "Location_Political", 0.97, 5120),
    ("California",            "Location_Political", 0.90, 2440),
    ("New York",              "Location_Political", 0.89, 2310),
    ("Washington",            "Location_Political", 0.86, 1890),
    ("Silicon Valley",        "Location_Physical",  0.82, 1340),
    ("Wall Street",           "Location_Physical",  0.83, 1420),
    ("iPhone",                "Product",            0.88, 2010),
    ("ChatGPT",               "Product",            0.87, 1930),
    ("Model 3",               "Product",            0.74, 720),
    ("S&P 500",               "FinancialFigure",    0.85, 1710),
    ("Dow Jones",             "FinancialFigure",    0.82, 1380),
    ("FOMC Meeting",          "Event",              0.76, 810),
    ("WWDC",                  "Event",              0.71, 620),
    ("Congress",              "Group_NationalOrReligious", 0.88, 2080),
    ("Q1 2026",               "TemporalRef",        0.60, 340),
]

# (source, target, relation, strength)
EDGES = [
    ("Elon Musk", "Tesla",              "leads",         0.95),
    ("Tesla", "Elon Musk",              "led_by",        0.95),
    ("Tim Cook", "Apple",               "leads",         0.94),
    ("Apple", "Tim Cook",               "led_by",        0.94),
    ("Sundar Pichai", "Google",         "leads",         0.94),
    ("Google", "Sundar Pichai",         "led_by",        0.94),
    ("Satya Nadella", "Microsoft",      "leads",         0.93),
    ("Microsoft", "Satya Nadella",      "led_by",        0.93),
    ("Sam Altman", "OpenAI",            "leads",         0.93),
    ("OpenAI", "Sam Altman",            "led_by",        0.93),
    ("Jerome Powell", "Federal Reserve","leads",         0.92),
    ("Federal Reserve", "Jerome Powell","led_by",        0.92),
    ("Microsoft", "OpenAI",             "invests_in",    0.88),
    ("OpenAI", "ChatGPT",               "makes",         0.91),
    ("Apple", "iPhone",                 "makes",         0.92),
    ("Tesla", "Model 3",                "makes",         0.86),
    ("Google", "Apple",                 "co_occurs",     0.74),
    ("Google", "Microsoft",             "co_occurs",     0.72),
    ("Apple", "Microsoft",              "co_occurs",     0.70),
    ("Amazon", "Google",                "co_occurs",     0.69),
    ("Google", "Silicon Valley",        "located_in",    0.80),
    ("Apple", "Silicon Valley",         "located_in",    0.80),
    ("Apple", "California",             "located_in",    0.78),
    ("Goldman Sachs", "Wall Street",    "located_in",    0.82),
    ("JPMorgan Chase", "Wall Street",   "located_in",    0.82),
    ("JPMorgan Chase", "Jane Fraser",   "co_occurs",     0.55),
    ("Federal Reserve", "FOMC Meeting", "hosts",         0.84),
    ("Federal Reserve", "Jerome Powell","co_occurs",     0.90),
    ("SEC", "Tesla",                    "regulates",     0.68),
    ("SEC", "Wall Street",              "co_occurs",     0.71),
    ("Janet Yellen", "United States",   "serves",        0.79),
    ("Jerome Powell", "Congress",       "testifies_to",  0.73),
    ("Warren Buffett", "S&P 500",       "co_occurs",     0.66),
    ("Apple", "WWDC",                   "hosts",         0.81),
    ("Opportunity Finance Network", "CDFI Fund", "partners_with", 0.75),
    ("Accion", "Opportunity Finance Network", "co_occurs", 0.58),
    ("Community Plan, Inc.", "Joshua Fitzgerald", "founded_by", 0.85),
    ("Joshua Fitzgerald", "Community Plan, Inc.", "founded",    0.85),
    ("Community Plan, Inc.", "CDFI Fund", "co_occurs",   0.48),
    ("Reuters", "Federal Reserve",      "covers",        0.64),
    ("Reuters", "Wall Street",          "covers",        0.63),
]

CRAWLED_URLS = [
    "https://www.reuters.com/markets/",
    "https://www.reuters.com/technology/",
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany",
    "https://en.wikipedia.org/wiki/Alphabet_Inc.",
    "https://en.wikipedia.org/wiki/Apple_Inc.",
    "https://en.wikipedia.org/wiki/Federal_Reserve",
    "https://www.congress.gov/",
    "https://arxiv.org/list/cs.CL/recent",
    "https://www.forbes.com/lists/",
    "https://techcrunch.com/",
    "https://www.bloomberg.com/markets",
    "https://ofn.org/",
    "https://www.cdfifund.gov/",
    "https://www.cfpb.gov/",
    "https://www.fdic.gov/",
    "https://www.sba.gov/",
]


def main():
    rng = random.Random(42)
    now = time.time()

    db.init_db()

    for name, tag, weight, freq in ENTITIES:
        # Stagger last_seen up to 20 days back so temporal decay is visible
        last_seen = now - rng.uniform(0, 20) * 86400
        db.execute(
            "INSERT INTO entities (name, tag, weight, frequency, last_seen, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            + ("ON CONFLICT (name) DO NOTHING" if db.USE_POSTGRES else "ON CONFLICT DO NOTHING"),
            (name, tag, weight, freq, last_seen, "{}"),
        )

    for source, target, relation, strength in EDGES:
        db.execute(
            "INSERT INTO edges (source, target, relation, strength) VALUES (?, ?, ?, ?) "
            + ("ON CONFLICT (source, target, relation) DO NOTHING" if db.USE_POSTGRES else "ON CONFLICT DO NOTHING"),
            (source, target, relation, strength),
        )

    for i, url in enumerate(CRAWLED_URLS):
        db.execute(
            "INSERT INTO crawled_urls (url, crawled_at, entity_count) VALUES (?, ?, ?) "
            + ("ON CONFLICT (url) DO NOTHING" if db.USE_POSTGRES else "ON CONFLICT DO NOTHING"),
            (url, now - i * 3600, rng.randint(8, 45)),
        )

    n_entities = db.query("SELECT COUNT(*) as n FROM entities", one=True)["n"]
    n_edges = db.query("SELECT COUNT(*) as n FROM edges", one=True)["n"]
    n_urls = db.query("SELECT COUNT(*) as n FROM crawled_urls", one=True)["n"]
    backend = "PostgreSQL" if db.USE_POSTGRES else f"SQLite ({db.SQLITE_PATH})"
    print(f"Seeded {backend}: {n_entities} entities, {n_edges} edges, {n_urls} crawled URLs.")


if __name__ == "__main__":
    main()
