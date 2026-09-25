# News Tunneler — Compiled System Reference

**Designation:** ntl
**Document role:** Canonical compiled technical reference for News Tunneler (local workspace directory: `TradeForge`)
**Source:** `doc/system/`
**Build command:** `bash doc/system/BUILD.sh`
**Document version:** 1.0 (2026-09-24) — initial doc/system authored from scratch
**Protocol:** BDS Documentation Protocol v2.0

> **Generated artifact warning:** `doc/ntlSYSTEM.md` is assembled output.
> Edit the source modules under `doc/system/` and rebuild. Hand edits to
> generated artifacts are overwritten by the next build.

**Naming note:** this repo's real product identity is **News Tunneler**
(its own README, GitHub repo name, and frontend branding). The local
workspace directory name `TradeForge` is an alias only — see
`01-overview-philosophy.md`. The designation `ntl` reflects the real name.

This `doc/system/` tree is the canonical source of truth for News Tunneler.
It uses explicit **truth classes**: canonical facts define role,
architecture, and API surface; snapshot facts are dated, audit-derived
observations (test counts, current scoring weights) that must be
re-measured before reuse.

Assembly contract:

- Command: `bash doc/system/BUILD.sh`
- Validation: `bash doc/system/validate_snapshots.sh` runs during assembly
- Primary output: `doc/ntlSYSTEM.md`

| Part | File | Contents |
| --- | --- | --- |
| §1 | `01-overview-philosophy.md` | Purpose and the naming-alias disclosure |
| §2 | `02-architecture.md` | FastAPI backend + SolidJS frontend, ML/scoring pipeline |
| §3 | `03-tech-stack.md` | Stack details |
| §4 | `04-project-structure.md` | Directory layout |
| §5 | `05-config-env.md` | Required/optional environment variables |
| §6 | `06-api-contract.md` | Route groups and scoring algorithm summary |
| §7 | `07-testing.md` | Test commands |
| §8 | `90-handover.md` | Deployment notes and chapter-authoring caveats |

## Quick Assembly

```bash
bash doc/system/BUILD.sh
```

---

# Overview and Philosophy

**Canonical fact — naming:** this repository's local directory name in this
workspace is `TradeForge`, but its actual product identity — the name in
its own README, its GitHub repository name, and its frontend branding — is
**News Tunneler**. This `doc/system/` tree documents it as News Tunneler.
Treat "TradeForge" as a local workspace alias only, not the product's real
name, when writing anything user-facing or cross-referencing this repo
elsewhere.

News Tunneler aggregates financial news from multiple RSS/Atom sources,
scores articles for trading relevance using a weighted algorithm plus
sentiment analysis, and surfaces ML-based next-day trading predictions and
AI-generated trading plans.

**Canonical fact:** this is a real-money-adjacent analytics tool (trading
signals, backtesting) but does not itself execute trades — it is a signal
and analysis platform, not a trading bot, based on the API surface and
feature set found in this repo.

---

# Architecture

News Tunneler is a FastAPI backend with a SolidJS frontend, backed by
Postgres (or SQLite for development), Redis, and Celery for async work.

**Canonical fact — backend (`backend/app/`):**

- `core/` — core functionality: scoring, sentiment analysis, ML
- `models/` — SQLAlchemy ORM models
- `api/` — FastAPI route handlers
- `tasks/` — Celery async tasks
- `ml/` — ML pipeline and models (scikit-learn, XGBoost, LightGBM, PyTorch,
  per the tech stack)
- `seeds/` — database seed data (sources, tickers)
- `services/`, `middleware/`, `jobs/`, `cli/`, `train/`, `data/`,
  `templates/` — supporting modules not further broken down here; consult
  each directly

**Canonical fact:** the backend has two entry points, `main.py` and
`main_minimal.py`. This chapter does not establish the difference between
them — check both directly before assuming which one is the production
entry point.

**Canonical fact — streaming:** the API exposes both WebSocket (`/ws/alerts`)
and Server-Sent Events (price/sentiment streams) for real-time updates,
per the API route surface described in the README.

**Canonical fact — frontend:** a SolidJS + TypeScript application using
ApexCharts for live charting, communicating with the backend over REST plus
the WebSocket/SSE channels above.

---

# Tech Stack

**Canonical fact — backend:**

- FastAPI (Python 3.12+)
- PostgreSQL (production) or SQLite (development), toggled by
  `USE_POSTGRESQL`/`DATABASE_URL` — see `05-config-env.md`
- SQLAlchemy 2.0 + Alembic (migrations)
- Redis (caching, Celery broker)
- Celery (async task queue)
- ML: scikit-learn, XGBoost, LightGBM, PyTorch
- LLM: OpenAI GPT-4 (requires `OPENAI_API_KEY`)
- Data: pandas, `yfinance`

**Canonical fact — frontend:** SolidJS 1.8+ (confirmed directly in
`frontend/package.json`), TypeScript, Vite, Tailwind CSS, ApexCharts.

**Canonical fact — infrastructure:** Docker + Docker Compose, Prometheus +
Grafana (monitoring), Sentry (error tracking).

---

# Project Structure

```text
backend/
  app/
    core/       Scoring, sentiment, ML core logic
    models/     SQLAlchemy ORM models
    api/        FastAPI route handlers
    tasks/      Celery async tasks
    ml/         ML pipeline and models
    seeds/      Database seed data (sources, tickers)
    services/, middleware/, jobs/, cli/, train/, data/, templates/
  alembic/      Database migrations
  tests/        Unit tests
  main.py, main_minimal.py   Two backend entry points (see 02-architecture.md)
frontend/
  src/
    components/   Reusable UI components
    pages/        Page components
    lib/          Utilities and state
  public/         Static assets
```

---

# Configuration and Environment

Configuration is Pydantic-`Settings`-based (`backend/app/core/config.py`).

**Canonical fact — required:**

- `OPENAI_API_KEY` — used for LLM-based analysis and trading-plan generation.

**Canonical fact — database (per the repo's own README; not re-verified
field-by-field in this chapter):**

- `USE_POSTGRESQL` (bool) and `DATABASE_URL` together select Postgres vs.
  the SQLite development default (`sqlite:///./app.db`).

**Canonical fact — Redis / Celery:**

- `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`.

**Canonical fact — optional:**

- `POLYGON_API_KEY`, `NEWSAPI_KEY` — additional data sources.
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`,
  `REPORT_RECIPIENTS` — email digests.
- `SENTRY_DSN`, `PROMETHEUS_ENABLED` — monitoring.
- `POLL_INTERVAL_SEC` — RSS polling interval, default 1800s (30 min) per the
  README.

**Frontend:** `VITE_API_BASE`, `VITE_WS_URL`.

**Not yet established here:** the exact set of fields in the `Settings`
class was not exhaustively cross-checked against this list — treat the
above as the README's own documented contract, verify directly in
`backend/app/core/config.py` before relying on any single variable.

---

# API Contract

Full interactive documentation is served by FastAPI itself at
`/docs` (Swagger UI) when the backend is running — that is the authoritative,
always-current contract. This chapter is a navigational summary only.

**Canonical fact — route groups (per the repo's own README):**

- Articles & alerts: `GET /api/articles`, `GET /api/articles/{id}`
- ML signals: `GET /api/signals/top-predictions`,
  `GET /api/signals/predict-tomorrow/{symbol}`,
  `GET /api/signals/tickers/{symbol}/score`
- Intraday bounds: `GET /api/predict/intraday-bounds/{ticker}`,
  `POST /api/predict/intraday-bounds/batch`
- Analysis & backtesting: `GET /api/analysis/summary/{ticker}`,
  `GET /api/backtest/{ticker}`
- Real-time streaming: `GET /api/stream/price/{symbol}` (SSE),
  `GET /api/stream/sentiment/{symbol}` (SSE), `WS /ws/alerts`

**Canonical fact — scoring algorithm:** each article receives a 0-100 score
from five weighted factors — Catalyst, Novelty, Credibility, Sentiment,
Liquidity. The exact current weights and thresholds are configuration, not
fixed facts, and should be read from `backend/app/core/` directly rather
than assumed from this chapter.

**Snapshot fact:** signal tiers as described in the repo's own README —
High-Conviction (70-100), Opportunity (50-69), Watch (30-49) — are a
point-in-time description of the current scheme, not an immutable contract.

---

# Testing

**Canonical fact:**

```bash
cd backend
source venv/bin/activate
pytest
pytest --cov=app --cov-report=html
pytest tests/test_scoring.py   # run a single test file
```

**Snapshot fact:** this chapter deliberately does not restate any specific
pass/fail count from this repo's own README — that is a dated,
audit-derived number that belongs with whatever CI run produced it, not
duplicated here where it would go stale.

---

# Handover

**Canonical fact:** this repo's real product identity is **News Tunneler**,
not "TradeForge" (the local workspace directory name). See
`01-overview-philosophy.md`.

**Operator note — deployment:** the repo ships `render.yaml` for one-click
Render deployment (recommended by the repo's own README), plus Docker
Compose for self-hosting. The astrological-synthesis-style constraint that
appears in other repos in this workspace does not apply here — this repo
has no Python-runtime-only feature comparable to that.

**Known limitation of this chapter set:** authored from the repo's own
README plus direct spot-checks of `backend/app/`'s directory layout,
`frontend/package.json`'s framework choice, and the existence of
`backend/app/core/config.py`. The exact `Settings` field list, the
difference between `main.py` and `main_minimal.py`, and the current scoring
weights were not independently re-derived from source — verify directly
before relying on specifics beyond what's stated here.
