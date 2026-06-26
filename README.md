# Aviation M&A & Strategic Partnership Deal Tracker

A data pipeline + dashboard that tracks aviation industry M&A, joint ventures,
codeshares, equity stakes, and tech partnerships, and surfaces where the
industry is converging on **build vs. buy vs. partner** by capability area
(MRO, loyalty tech, regional connectivity, next-gen aircraft, IT/cloud
infrastructure, sustainability).

Built as a working artifact to demonstrate how a Corporate Development /
competitive intelligence workflow could be supported by a lightweight,
reproducible internal tool — not a slide deck.

## Why this exists

Corp Dev teams at major airlines track deal flow across competitors and
adjacent capability areas to inform their own build-vs-buy-vs-partner
decisions. This project models that workflow end-to-end: a structured,
sourced dataset of real deals, a validated ETL pipeline, and an interactive
dashboard for slicing deal activity by type, region, capability area, and
strategic posture.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Data store | SQLite | Zero-config, reproducible by anyone who clones the repo — no cloud credentials needed to run it |
| ETL / validation | Python, pandas, Pydantic | Pydantic schema catches malformed rows (bad enums, missing rationale, negative deal values) before they hit the database |
| Dashboard | Streamlit + Plotly | Fast to build, easy for a non-technical reviewer to run locally |
| Tests | pytest | Validates schema enforcement and the load pipeline itself |

## Data source

The dataset (`data/raw/deals_seed.csv`) is a **manually curated seed dataset**
of ~50 real, publicly reported aviation deals from 2008–2024, each with a
named source (DOJ/DOT press releases, SEC/10-K filings, company press
releases, or trade press) and a source URL. This was chosen over scraping a
news API because:

- Free news APIs are unreliable for extracting structured fields (deal type,
  value, capability area, build/buy/partner posture) without a much larger
  NLP/entity-extraction effort.
- M&A deal terms (value, structure, status) are frequently revised after
  announcement — a curated dataset lets each row be checked against a
  primary source rather than trusting article text at scrape time.
- For a portfolio piece, data *quality and traceability* matter more than
  pipeline automation. Every row can be defended in an interview.

The schema and pipeline are source-agnostic — extending `etl/load.py` to pull
from an RSS feed or news API later is a matter of producing a CSV/DataFrame
in the same shape; the validation and SQLite load logic don't change.

## Project structure

```
.
├── data/
│   ├── raw/deals_seed.csv       # curated seed dataset (source of truth)
│   └── processed/deals.db       # SQLite output of the ETL run (gitignored)
├── etl/
│   ├── schema.py                # Pydantic models: deal types, enums, validators
│   └── load.py                  # CSV -> validate -> SQLite
├── dashboard/
│   └── app.py                   # Streamlit app
├── tests/
│   └── test_etl.py              # schema + pipeline tests
└── requirements.txt
```

## Running it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Build the database from the seed CSV
python -m etl.load

# Launch the dashboard
streamlit run dashboard/app.py
```

Run tests with:

```bash
pytest tests/ -v
```

## Dashboard features

- **Filters**: year range, deal type, region, capability area, build/buy/partner posture
- **KPIs**: deal count, disclosed deal value, most active capability area, partner-led share
- **Pattern charts**: deal activity by capability area, build/buy/partner mix by capability area, deal volume over time by type, disclosed deal value by region
- **Build vs. buy vs. partner read-out**: dominant strategic posture per capability area
- **Deal log**: sortable/filterable table with per-deal rationale and sourcing

## Extending this

- Add a scheduled job (RSS/news API) that appends new deals to a review queue
  rather than auto-publishing — keeps the "every row is sourced" guarantee.
- Swap SQLite for Snowflake/Databricks if deploying for a team rather than as
  a portfolio artifact — the ETL/schema layer doesn't need to change.
- Add a weighted scoring model (strategic fit, integration risk, capital
  intensity) on top of the existing build/buy/partner tagging.
