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
