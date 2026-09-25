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
