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
