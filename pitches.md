# 3XB Sales Pitches

---

## 1. Opportunity Finance Network
**Contact:** info@opportunityfinance.net
**Angle:** Tool for their 400 CDFI members to underwrite thin-file borrowers

**Subject:** Alternative underwriting data for CDFI members — live API demo

Hi,

I'm reaching out because Opportunity Finance Network members face a common problem: borrowers with strong web presence and community ties but thin credit files get declined on FICO alone.

I've built 3XB — a web entity intelligence system that scores loan applicants based on their real-world prominence, relationships, and network graph across 114,000+ entities crawled from news, SEC filings, Wikipedia, and financial sources.

One API call returns:
- The borrower's web prominence weight (0–1 scale)
- Their 2-hop relationship risk score (co-signers, prior companies, backers)
- A composite APPROVE / REVIEW / DECLINE recommendation

Live demo: https://api.earthenwarecomputer.com/docs
Try it: https://api.earthenwarecomputer.com/entity/Google/loan-score

I'd love to explore whether this fits as a tool for OFN members. Would you have 20 minutes this month?

Joshua Fitzgerald
Community Plan, Inc.
almeidacorporation20@gmail.com

---

## 2. Battlefin (Alternative Data Marketplace)
**Contact:** https://battlefin.com/data-providers
**Angle:** List 3XB entity weight + frequency time series as a dataset product

**Subject:** New alternative dataset — web entity prominence scores, 114K entities

Hi Battlefin team,

I'd like to list a new alternative dataset on your marketplace.

**3XB Web Entity Intelligence** tracks 114,000+ named entities (people, organizations, locations) across the web — scoring each by prominence, frequency, and relationship graph. The dataset updates continuously as new pages are crawled.

What buyers get:
- Entity weight scores (0–1) derived from 480,000+ co-occurrence relationships
- Temporal decay signals — scores degrade without fresh web mentions
- Person / Org / Location breakdown across 30+ seed domains (Reuters, SEC, arXiv, Congress, Forbes, TechCrunch)
- REST API access or raw data export

This is a natural fit for quant funds tracking company/person prominence ahead of news cycles.

Live API: https://api.earthenwarecomputer.com
Dataset docs: https://api.earthenwarecomputer.com/docs

Happy to provide a sample export or walk through the methodology.

Joshua Fitzgerald
almeidacorporation20@gmail.com

---

## 3. In-Q-Tel
**Contact:** https://www.iqt.org/submit-your-company/
**Angle:** Entity influence graph for intelligence / national security applications

**Subject:** Web-scale entity influence graph — relationship propagation for threat analysis

To the In-Q-Tel team,

I'm submitting 3XB — a web entity intelligence system that builds a live weighted graph of people, organizations, and locations extracted from across the internet.

What makes it relevant to your portfolio:

- **114,000+ entities** tagged from news, government filings, academic sources, and financial data
- **480,000 relationship edges** built from co-occurrence — entities appearing together get linked
- **Risk propagation** — influence and risk scores flow 2+ hops through the graph (if Entity A is connected to Entity B, B's score affects A)
- **Temporal decay** — entity weights degrade without fresh signals, keeping the graph current
- **X/social signal injection** — live signal hooks to boost entity weight from real-time sources

The system is live at: https://api.earthenwarecomputer.com

Applications include influence network mapping, entity prominence tracking, and relationship-based risk scoring — all from open-source web data.

Joshua Fitzgerald
Community Plan, Inc.
almeidacorporation20@gmail.com

---

## 4. Accion
**Contact:** https://www.accion.org/contact
**Angle:** Drop-in underwriting tool for their microloan portfolio

**Subject:** Alternative credit scoring for micro-borrowers — live demo

Hi Accion team,

Accion serves entrepreneurs who often lack traditional credit history but have real-world traction — web presence, press mentions, business relationships. 3XB turns that signal into a loan score.

Here's how it works:
- We crawl 4,000+ pages daily across news, SEC filings, Wikipedia, and business sources
- Every person and organization gets a prominence weight (0–1) based on frequency and relationship graph
- One API call to `/entity/{borrower}/loan-score` returns APPROVE / REVIEW / DECLINE with a composite score

This is built specifically for the lending gap Accion serves — borrowers that FICO misses but the web can validate.

Live demo (try any name): https://api.earthenwarecomputer.com/entity/Google/loan-score
Full API: https://api.earthenwarecomputer.com/docs

I'd welcome a conversation about integrating this into Accion's underwriting workflow.

Joshua Fitzgerald
Community Plan, Inc.
almeidacorporation20@gmail.com
