# News Tunneler Backend

FastAPI-based backend for real-time news scoring and alerting.

## Quick Start

### Prerequisites
- Python 3.12+
- pip or poetry

### Installation

```bash
# Install dependencies
make install

# Or manually
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Key environment variables:
- `DATABASE_URL`: SQLite path (default: `sqlite:///./data/news.db`)
- `POLL_INTERVAL_SEC`: Feed polling interval in seconds (default: 900)
- `MIN_ALERT_SCORE`: Minimum score to trigger alerts (default: 12)
- `SLACK_WEBHOOK_URL`: Optional Slack webhook for notifications
- `SMTP_*`: Optional email configuration

### Database Setup

```bash
# Create tables
make migrate

# Seed with sample data
make seed
```

### Running

**Development:**
```bash
make dev
```

Server runs at `http://localhost:8000`

**Production:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API docs.

### Key Endpoints

**Articles:**
- `GET /api/articles` - List articles with filtering
- `GET /api/articles/{id}` - Get single article
- Query params: `q`, `min_score`, `ticker`, `domain`, `since`, `limit`, `offset`

**Sources:**
- `GET /api/sources` - List all sources
- `POST /api/sources` - Add new RSS/Atom feed
- `PATCH /api/sources/{id}` - Enable/disable source
- `DELETE /api/sources/{id}` - Delete source

**Settings:**
- `GET /api/settings` - Get current settings
- `PATCH /api/settings` - Update weights and thresholds

**WebSocket:**
- `WS /ws/alerts` - Real-time alert stream

**Health:**
- `GET /health` - Health check
- `GET /` - API info

## Testing

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_scoring.py -v

# Run with coverage
pytest tests/ --cov=app
```

## Code Quality

```bash
# Lint
make lint

# Format
make format
```

## Architecture

### Core Modules

- **config.py**: Environment configuration
- **db.py**: Database connection and session management
- **scoring.py**: Article scoring logic
- **sentiment.py**: VADER sentiment analysis
- **rss.py**: RSS/Atom feed fetching
- **dedupe.py**: Article deduplication
- **tickers.py**: Ticker symbol extraction
- **notifiers.py**: Slack/Email notifications
- **scheduler.py**: Background feed polling

### Models

- **Source**: RSS/Atom feeds
- **Article**: News articles
- **Score**: Computed scores for articles
- **Setting**: User preferences and weights
- **Webhook**: Notification endpoints

### Scoring Algorithm

Total Score = (Catalyst × w_catalyst) + (Novelty × w_novelty) + (Credibility × w_credibility) + (Sentiment × w_sentiment) + (Liquidity × w_liquidity)

**Catalyst (0-5):**
- 5: 8-K, guidance, beat, miss, acquire, merger, FDA, PDUFA, contract, award, buyback, investigation, export ban
- 3: trial, phase, partnership, license, MoU
- 0: other

**Novelty (0-5):**
- 5: < 6 hours old
- 3: < 24 hours old
- 1: >= 24 hours old

**Credibility (0-5):**
- 5: sec.gov, investor.*, ir.*, prnewswire, globenewswire, businesswire
- 3: other sources

**Sentiment (1-4):**
- 1: negative (VADER compound ≤ -0.2)
- 3: neutral (-0.2 < compound < 0.2)
- 4: positive (compound ≥ 0.2)

**Liquidity (0-5):**
- Currently 0 (placeholder for volume API integration)

## Extending

See `docs/EXTENDING.md` for:
- Adding new scoring rules
- Integrating new data sources
- Creating custom notifiers
- Adding new API endpoints

## Troubleshooting

**Database locked error:**
```bash
# Remove old database
rm data/news.db
make migrate
make seed
```

**Feed parsing errors:**
Check logs for specific feed URLs. Some feeds may require special handling.

**Notifications not working:**
- Slack: Verify webhook URL is correct
- Email: Check SMTP credentials and firewall rules

## License

MIT

