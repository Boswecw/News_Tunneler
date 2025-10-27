# News Tunneler

A production-ready, real-time news scoring system for identifying short-term trading catalysts. Pulls from RSS/Atom feeds and NewsAPI, scores headlines using a multi-factor algorithm, and broadcasts alerts via REST API, WebSocket, and optional Slack/Email notifications.

## Features

### Backend
- **Multi-source ingestion**: RSS, Atom, NewsAPI
- **Intelligent scoring**: 5-factor algorithm (Catalyst, Novelty, Credibility, Sentiment, Liquidity)
- **Real-time alerts**: WebSocket + REST API
- **Notifications**: Slack, Email (with debouncing)
- **Database**: SQLite with SQLAlchemy ORM
- **Background jobs**: APScheduler for feed polling
- **API documentation**: Swagger/OpenAPI at `/docs`

### Frontend
- **Real-time dashboard**: Live alerts with WebSocket
- **Advanced filtering**: Search, score threshold, ticker filtering
- **Source management**: Add/enable/disable feeds
- **Scoring controls**: Adjust weights and thresholds
- **Dark mode**: Light/dark theme toggle
- **Responsive design**: Mobile-friendly UI

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose (optional)

### Development

1. **Clone and setup**
```bash
cd news-tunneler
cp .env.example .env
```

2. **Install dependencies**
```bash
make install
```

3. **Start development servers**
```bash
make dev
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

### Docker

```bash
make docker-build
make docker-up
```

Access at http://localhost:5173

## Project Structure

```
news-tunneler/
├── backend/
│   ├── app/
│   │   ├── core/              # Configuration, database, scoring
│   │   ├── models/            # SQLAlchemy models
│   │   ├── api/               # FastAPI routes
│   │   ├── seeds/             # Sample data
│   │   └── main.py            # FastAPI app
│   ├── tests/                 # Unit tests
│   ├── alembic/               # Database migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── Makefile
├── frontend/
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Page components
│   │   ├── lib/               # API client, WebSocket, store
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── Dockerfile
│   └── Makefile
├── docker-compose.yml
├── .env.example
├── Makefile
└── README.md
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Backend
DATABASE_URL=sqlite:///./app.db
POLL_INTERVAL_SEC=900

# Optional: Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Optional: Email
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Optional: NewsAPI
NEWSAPI_KEY=your-newsapi-key

# Frontend
VITE_API_BASE=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/alerts
```

## API Endpoints

### Articles
- `GET /api/articles` - List articles with filtering
- `GET /api/articles/{id}` - Get article details

### Sources
- `GET /api/sources` - List all sources
- `POST /api/sources` - Add new source
- `PATCH /api/sources/{id}` - Enable/disable source
- `DELETE /api/sources/{id}` - Delete source

### Settings
- `GET /api/settings` - Get scoring settings
- `PATCH /api/settings` - Update weights and thresholds

### WebSocket
- `WS /ws/alerts` - Real-time alert stream

### Health
- `GET /health` - Health check

## Scoring Algorithm

```
Total Score = (Catalyst × w_catalyst) 
            + (Novelty × w_novelty) 
            + (Credibility × w_credibility) 
            + (Sentiment × w_sentiment) 
            + (Liquidity × w_liquidity)
```

### Components

- **Catalyst (0-5)**: Keyword-based detection (merger, FDA, earnings, etc.)
- **Novelty (0-5)**: Time-based (5 if <6h, 3 if <24h, 1 otherwise)
- **Credibility (0-5)**: Domain-based (5 for trusted sources)
- **Sentiment (1-4)**: VADER compound score mapping
- **Liquidity (0-5)**: Placeholder for volume API integration

### Default Threshold
- Minimum alert score: 12

## Database

SQLite with SQLAlchemy ORM. Schema includes:

- **Source**: RSS/Atom/NewsAPI feeds
- **Article**: News articles with scores
- **Score**: Detailed scoring breakdown
- **Setting**: Configurable weights and thresholds
- **Webhook**: Notification history

Migrations managed with Alembic.

## Testing

```bash
make test-backend
```

Includes tests for:
- Scoring algorithm
- Article deduplication
- API endpoints

## Deployment

### Docker Compose
```bash
docker-compose up -d
```

### Manual
```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run build
npm run preview
```

## Development

### Backend
- Framework: FastAPI
- ORM: SQLAlchemy 2.0
- Async: asyncio + httpx
- Scheduler: APScheduler
- Testing: pytest

### Frontend
- Framework: SolidJS
- Build: Vite
- Styling: Tailwind CSS
- State: Zustand
- HTTP: Axios

## Optional Features

- ✅ Slack/Email notifications with debouncing
- ✅ NewsAPI integration
- ✅ Admin token authentication
- ✅ CSV export (ready to implement)
- ✅ SEC quick links (ready to implement)
- ✅ Score breakdown tooltips (ready to implement)

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.12+

# Install dependencies
pip install -r backend/requirements.txt

# Run migrations
cd backend && alembic upgrade head
```

### Frontend won't connect
```bash
# Check API is running
curl http://localhost:8000/health

# Check environment variables
cat frontend/.env.local
```

### WebSocket connection fails
- Ensure backend is running
- Check VITE_WS_URL in frontend/.env.local
- Check browser console for errors

## License

MIT

## Support

For issues or questions, check the documentation or open an issue.

