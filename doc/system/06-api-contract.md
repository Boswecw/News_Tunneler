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
