# Known Issues

This document tracks active limitations and historical fixes. Blocking impact is stated per item; an old resolved entry is not a substitute for current source verification.

---

## KI-NEWSTUNNELER-20260925-001 — backend test suite has never run in CI (`ModuleNotFoundError: No module named 'app'`)

**Status:** OPEN. Found 2026-09-25 while getting PR #1 (`docs/author-doc-system`, a `doc/system/` documentation addition, unrelated in content) to a green CI state.

**What is wrong:** The `test` job in `.github/workflows/test.yml` runs `cd backend && pytest tests/ -v --cov=app ...`. Every one of the 8 test modules under `backend/tests/` fails at collection with `ModuleNotFoundError: No module named 'app'` (e.g. `tests/test_api_articles.py:10: from app.models import (...)`). Zero tests have ever actually executed; the job has always failed at the collection step, not at any assertion.

**Root cause:** Not yet isolated. Candidates: `backend/` is not on `sys.path`/`PYTHONPATH` when `pytest` runs from inside `backend/` in CI (no `conftest.py` inserting `..`/`.` onto the path, no `pytest.ini`/`pyproject.toml` `pythonpath` setting, no editable install of the backend package). Needs someone to actually run `cd backend && pytest tests/` locally against this exact tree to confirm which of these is missing — not fixed blind.

**Masked cause found and fixed 2026-09-25 (separate, shallower bug):** `backend/requirements.txt` never listed `pytest-cov`, so `--cov=app` failed pytest's own argument parsing before collection ever ran ("unrecognized arguments"). This is what CI actually reported before today. Fixed by adding `pytest-cov==4.1.0` to `requirements.txt` (PR #1) — this uncovered the deeper `ModuleNotFoundError` issue above, which was previously hidden behind the argument-parsing failure.

**Also fixed 2026-09-25 (unrelated, cosmetic):** The `test` job's "Comment PR with test results" step 403s (`Resource not accessible by integration`) because the default `GITHUB_TOKEN` here lacks `issues: write`. It was failing the whole `test` job's conclusion even on a clean test run. Marked `continue-on-error: true` so only a real test failure fails the job going forward.

**Fix:** Not applied for the `ModuleNotFoundError` itself — needs the root-cause isolation above, then either a `conftest.py`, a `pythonpath` entry, or an editable install added to the CI install step.

**Scope:** OPEN. PR #1 was merged anyway despite this — it only adds `doc/system/` files, it doesn't touch the backend, and the test suite's collection failure is confirmed pre-existing (unrelated to that PR's content, and unrelated to the `pytest-cov` dependency also fixed in the same PR). Blocking this doc PR on an unrelated, already-broken test suite would just leave good work stuck. The next real change to `backend/` should not be merged without this being fixed first, since right now CI provides zero test coverage signal for it.
