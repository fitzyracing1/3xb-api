# Product Hunt Listing — 3XB Web Entity Intelligence API

---

## Tagline (60 chars max)
Web entity intelligence API — score any person or org from live web data

---

## Description (260 chars max — for the listing card)
3XB crawls the internet in real time, scores 137,000+ named entities by web prominence and relationship graph, and returns APPROVE / REVIEW / DECLINE loan verdicts via one API call. Built for CDFIs, alt data buyers, and NLP researchers.

---

## Full Description (for the product page)

**The problem:** Community lenders turn away good borrowers every day because FICO doesn't capture web presence, business relationships, or real-world prominence. Meanwhile, quant funds and compliance teams need entity intelligence that updates in real time — not quarterly data dumps.

**What 3XB does:**

3XB crawls 4,000+ pages daily across Reuters, SEC filings, Wikipedia, arXiv, Congress.gov, Forbes, TechCrunch, and 40+ other sources. Every named person, organization, and location gets:

- A **prominence weight** (0–1) based on how often and where they appear across the web
- A **relationship graph** — 593,000+ co-occurrence edges linking entities that appear together
- **Temporal decay** — scores fade without fresh mentions, keeping data current automatically
- A **loan score** — composite APPROVE / REVIEW / DECLINE built from own weight + 2-hop neighbor risk propagation

**One API call:**
```
GET /entity/Elon Musk/loan-score
→ { "composite_score": 0.9526, "recommendation": "APPROVE" }
```

**Who it's for:**

🏦 **CDFIs and community lenders** — score thin-file borrowers using web prominence instead of FICO. Built for the 1,383 certified CDFIs in the US who serve borrowers traditional banks decline.

📈 **Quant funds and alt data buyers** — entity prominence time series as a systematic signal. Track how a company or person's web presence shifts ahead of news cycles.

🔍 **Compliance teams** — entity risk scoring and relationship propagation for KYC/AML workflows.

🧠 **NLP researchers** — 137,000+ tagged entities, 593,000+ relationship edges, exportable as JSON or CSV.

**What's live today:**
- 137,000+ unique entities tagged
- 593,000+ relationship edges
- REST API with 10 endpoints
- CSV export with loan scores
- Stripe subscription billing

**Try it free:**
https://api.earthenwarecomputer.com/entity/Google/loan-score

**Full API docs:**
https://api.earthenwarecomputer.com/docs

---

## First Comment (post this yourself right after launch)

Hey PH! 👋

I built 3XB after seeing how many good borrowers get turned away by CDFIs because FICO alone doesn't tell the whole story. A founder with 50 press mentions, SEC filings, and Wikipedia references is a very different risk than someone with the same FICO score and no web presence.

The core insight: the web already knows who matters. We just needed to score it.

Happy to answer questions about the crawling architecture, the 3XB weighting model, or how the loan score propagates risk through the relationship graph.

Try any name: https://api.earthenwarecomputer.com/entity/Google/loan-score

---

## Topics / Tags
alternative-data, fintech, api, machine-learning, nlp, developer-tools, finance, credit

---

## Links
- Website: https://earthenwarecomputer.com
- API: https://api.earthenwarecomputer.com
- Docs: https://api.earthenwarecomputer.com/docs

---

## Pricing
- Starter: $500/mo — 1,000 API calls
- Growth: $1,500/mo — 10,000 API calls
- Enterprise: Custom
