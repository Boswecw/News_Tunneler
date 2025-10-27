# Quick Start Guide

Get News Tunneler running in 5 minutes!

## Option 1: Docker (Easiest)

### Prerequisites
- Docker & Docker Compose installed

### Steps

```bash
# 1. Clone/navigate to project
cd news-tunneler

# 2. Copy environment file
cp .env.example .env

# 3. Build and start
make docker-build
make docker-up

# 4. Wait for services to start (30 seconds)
sleep 30

# 5. Open browser
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

Done! The system is running with sample data.

## Option 2: Local Development

### Prerequisites
- Python 3.12+
- Node.js 18+
- pip, npm

### Steps

```bash
# 1. Navigate to project
cd news-tunneler

# 2. Copy environment file
cp .env.example .env

# 3. Install dependencies
make install

# 4. Start development servers
make dev
```

This starts:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

## First Steps

### 1. View Dashboard
Open http://localhost:5173 in your browser

You'll see:
- KPI cards (alerts, average score, top tickers)
- Live alerts table
- Real-time updates

### 2. Add a News Source
1. Click "Sources" in navigation
2. Click "Add New Source"
3. Enter a feed URL (e.g., `https://feeds.bloomberg.com/markets/news.rss`)
4. Give it a name
5. Click "Add Source"

### 3. Adjust Scoring Weights
1. Click "Settings"
2. Adjust the weight sliders (0-5 scale)
3. Set minimum alert threshold
4. Click "Save Settings"

### 4. Filter Alerts
1. Click "Alerts"
2. Use filters:
   - Search by keyword
   - Filter by minimum score
   - Filter by ticker symbol
3. Click "Apply Filters"

## Sample Data

The system comes pre-loaded with:
- 10 news sources (SEC, PR Newswire, GlobeNewswire, etc.)
- 20 sample articles
- Default scoring weights

To reseed:
```bash
make seed
```

## API Examples

### Get Articles
```bash
curl http://localhost:8000/api/articles?min_score=12&limit=10
```

### Get Settings
```bash
curl http://localhost:8000/api/settings
```

### Update Settings
```bash
curl -X PATCH http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"weight_catalyst": 1.5, "min_alert_score": 15}'
```

### Add Source
```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/feed.xml",
    "name": "Example Feed",
    "source_type": "rss"
  }'
```

## WebSocket Connection

Connect to real-time alerts:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/alerts');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'alert') {
    console.log('New alert:', message.data);
  }
};
```

## Configuration

### Environment Variables

Edit `.env` to configure:

```env
# Backend
DATABASE_URL=sqlite:///./app.db
POLL_INTERVAL_SEC=900  # Check feeds every 15 minutes

# Optional: Slack Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Optional: Email Notifications
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Optional: NewsAPI
NEWSAPI_KEY=your-newsapi-key
```

### Scoring Weights

Adjust in Settings page or via API:

```bash
curl -X PATCH http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "weight_catalyst": 1.5,
    "weight_novelty": 1.0,
    "weight_credibility": 1.2,
    "weight_sentiment": 0.8,
    "weight_liquidity": 1.0,
    "min_alert_score": 15
  }'
```

## Scoring Algorithm

Articles are scored on 5 factors:

1. **Catalyst** (0-5): Keywords like "merger", "FDA approval", "earnings beat"
2. **Novelty** (0-5): How recent (5 if <6h, 3 if <24h, 1 otherwise)
3. **Credibility** (0-5): Source reputation (5 for trusted sources)
4. **Sentiment** (1-4): Positive/negative tone analysis
5. **Liquidity** (0-5): Trading volume (placeholder)

**Total Score** = Sum of (Component × Weight)

Default threshold: 12 (alerts triggered for scores ≥ 12)

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Or manually
cd backend
python -m uvicorn app.main:app --reload
```

### Frontend won't connect
```bash
# Check API is running
curl http://localhost:8000/health

# Check environment variables
cat frontend/.env.local
```

### No articles appearing
```bash
# Check sources are enabled
curl http://localhost:8000/api/sources

# Manually trigger feed poll
# (Happens automatically every 15 minutes)
```

### WebSocket connection fails
- Ensure backend is running
- Check browser console for errors
- Verify VITE_WS_URL in frontend/.env.local

## Next Steps

1. **Add more sources**: Click "Sources" and add your favorite news feeds
2. **Customize scoring**: Adjust weights in "Settings" based on your strategy
3. **Set up notifications**: Configure Slack/Email in `.env`
4. **Integrate with trading**: Use the REST API or WebSocket in your trading system
5. **Deploy to production**: See [DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Documentation

- [README.md](README.md) - Project overview
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design
- [EXTENDING.md](docs/EXTENDING.md) - How to add features
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Production deployment

## Support

- Check logs: `docker-compose logs -f`
- Review API docs: http://localhost:8000/docs
- Check GitHub issues
- Read documentation

## Commands Reference

```bash
# Development
make dev              # Start both servers
make dev-backend      # Start backend only
make dev-frontend     # Start frontend only

# Building
make build            # Build both
make build-backend    # Build backend
make build-frontend   # Build frontend

# Testing
make test             # Run tests
make test-backend     # Run backend tests

# Database
make seed             # Seed sample data
make migrate          # Run migrations

# Docker
make docker-build     # Build images
make docker-up        # Start containers
make docker-down      # Stop containers
make docker-logs      # View logs

# Cleanup
make clean            # Remove build artifacts
```

Enjoy News Tunneler! 🚀

