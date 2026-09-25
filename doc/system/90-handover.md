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
