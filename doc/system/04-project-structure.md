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
