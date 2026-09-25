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
