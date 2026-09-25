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
