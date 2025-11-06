# 📰 News Tunneler

<div align="center">

![News Tunneler Logo](frontend/public/News_Tunneler_icon.webp)

**AI-Powered Trading Analytics Platform**

*Real-time market data + sentiment analysis + machine learning = High-conviction trading opportunities*

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

### 🚀 Deploy Now

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

[Quick Start](#-quick-start) • [Features](#-features) • [Deployment](#-deployment) • [API Reference](#-api-reference)

</div>

---

## 🎯 What It Does

News Tunneler aggregates financial news from 20+ premium sources, analyzes them using ML and LLM, and provides actionable trading signals with real-time market data visualization.

### Key Features

- **🤖 ML-Powered Predictions**: Next-day trading forecasts based on signal strength and sentiment
- **📊 Real-Time Streaming**: Live price and sentiment charts during market hours (9:30 AM - 4:00 PM ET)
- **🎯 Smart Signals**: Three-tier system (High-Conviction 70-100, Opportunity 50-69, Watch 30-49)
- **📈 Backtesting Engine**: Validate strategies against historical data
- **🔍 Multi-Source Intelligence**: SEC filings, financial news, FDA approvals, energy reports
- **💡 AI Trading Plans**: GPT-4 generated entry/exit strategies with risk management
- **📱 Progressive Web App**: Install on any device with offline support

---

## 🚀 Quick Start

### Local Development

**Prerequisites:**
- Python 3.12+
- Node.js 18+ or Bun
- OpenAI API Key

**1. Clone and Setup Backend:**

```bash
git clone https://github.com/Boswecw/News_Tunneler.git
cd News_Tunneler/backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run migrations
alembic upgrade head

# Seed initial data
python -m app.seeds.seed_sources
python -m app.seeds.seed_tickers

# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**2. Setup Frontend:**

```bash
cd ../frontend

# Install dependencies
bun install  # or: npm install

# Start development server
bun run dev  # or: npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🌐 Deployment

### Deploy to Render (Recommended)

**One-click deployment with managed PostgreSQL:**

1. **Click "Deploy to Render" button** above
2. **Configure environment variables:**
   ```env
   # Required
   OPENAI_API_KEY=sk-...

   # Database (auto-configured by Render)
   USE_POSTGRESQL=true
   DATABASE_URL=${DATABASE_URL}

   # Redis (optional - configure separately)
   # Use Upstash (free tier) or Redis Labs
   # See: https://upstash.com/
   REDIS_URL=redis://default:password@host:port
   CELERY_BROKER_URL=${REDIS_URL}
   CELERY_RESULT_BACKEND=${REDIS_URL}

   # Optional
   POLYGON_API_KEY=your-key
   SMTP_HOST=smtp.gmail.com
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

3. **Deploy!** Render automatically:
   - Builds and deploys your backend
   - Provisions PostgreSQL database
   - Runs database migrations
   - Configures SSL certificates
   - Sets up auto-deploy on git push

4. **(Optional) Add Redis for production:**
   - Create free Redis database at [Upstash](https://upstash.com/)
   - Copy the `REDIS_URL` connection string
   - Add to Render environment variables:
     - `REDIS_URL`
     - `CELERY_BROKER_URL` (same value)
     - `CELERY_RESULT_BACKEND` (same value)

5. **Seed data after first deploy:**
   ```bash
   # Connect to Render shell and run:
   python -m app.seeds.seed_sources
   python -m app.seeds.seed_tickers
   ```

**What's Included:**
- ✅ Backend API with auto-scaling
- ✅ PostgreSQL database (managed)
- ✅ Automatic SSL certificates
- ✅ Auto-deploy on git push
- ✅ Free tier available
- ⚠️ Redis cache requires external service (Upstash recommended)

**Pricing:** Free tier available, Starter plan $24/month

---

### Deploy with Docker (Self-Hosted)

**Quick start with Docker Compose:**

```bash
# Backend setup
cd backend
cp .env.example .env
# Add your OPENAI_API_KEY and other configs

# Start services
docker-compose up -d

# Run migrations
docker exec news-tunneler-backend alembic upgrade head

# Seed data
docker exec news-tunneler-backend python -m app.seeds.seed_sources
docker exec news-tunneler-backend python -m app.seeds.seed_tickers
```

**Services:**
- Backend: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- PgAdmin: http://localhost:5050

---

## ✨ Features

### Dashboard
- Real-time KPIs: Total articles, high-conviction signals, average score
- Recent alerts feed with live WebSocket updates
- Quick access to top opportunities

### Live Charts
- **Market Hours**: Real-time streaming price + sentiment (1-minute intervals)
- **After-Hours**: ML-generated predictions for next trading session
- **Intraday Bounds**: ML-powered high/low predictions (5/15/30-minute horizons)
- **Buy/Sell Signals**: Predicted optimal entry/exit points
- Auto-loading of top 5 predicted stocks

### Opportunities
- Ranked stocks with ML signals
- Signal labels: High-Conviction (70-100), Opportunity (50-69), Watch (30-49)
- Sentiment analysis with bullish/bearish indicators
- AI-generated trading plans
- Backtesting results

### Alerts
- Filterable table of all scored articles
- Search by ticker, keyword, or source
- Score breakdown tooltips (Catalyst, Novelty, Credibility, Sentiment, Liquidity)
- Direct links to original articles

### Sources
- Manage 20+ RSS/Atom feeds
- Enable/disable sources individually
- Add custom feeds with automatic parsing

### Settings
- Adjust scoring weights
- Configure alert thresholds
- Email digest settings
- Dark mode toggle

---

## 🛠️ Tech Stack

**Backend:**
- FastAPI 0.104+ (Python 3.12+)
- PostgreSQL 16 / SQLite 3
- SQLAlchemy 2.0 + Alembic
- Redis 7.0+ (caching + Celery broker)
- Celery 5.3+ (task queue)
- ML: scikit-learn, XGBoost, LightGBM, PyTorch
- LLM: OpenAI GPT-4
- Data: pandas, yfinance

**Frontend:**
- SolidJS 1.8+ with TypeScript 5.0+
- Vite 5.0+ build tool
- Tailwind CSS 3.4+
- ApexCharts 3.45+
- WebSocket + Server-Sent Events

**Infrastructure:**
- Docker + Docker Compose
- Prometheus + Grafana (monitoring)
- Sentry (error tracking)

---

## 📊 Scoring Algorithm

Each article receives a score from 0-100 based on five weighted factors:

```python
Total Score = (Catalyst × w_catalyst)
            + (Novelty × w_novelty)
            + (Credibility × w_credibility)
            + (Sentiment × w_sentiment)
            + (Liquidity × w_liquidity)
```

| Factor | Range | Description |
|--------|-------|-------------|
| **Catalyst** | 0-5 | Market-moving potential (merger, FDA approval, earnings) |
| **Novelty** | 0-5 | Time-based freshness (5 if <6h, 3 if <24h) |
| **Credibility** | 0-5 | Source trustworthiness (5 for WSJ/Bloomberg) |
| **Sentiment** | 1-4 | VADER sentiment analysis |
| **Liquidity** | 0-5 | Trading volume/ease |

**Default Weights:** Catalyst: 3.0, Novelty: 2.0, Credibility: 2.5, Sentiment: 1.5, Liquidity: 1.0

**Alert Threshold:** Articles scoring ≥12 trigger alerts

---

## 🔌 API Reference

### Key Endpoints

**Articles & Alerts**
```http
GET /api/articles?q={search}&min_score={score}&ticker={symbol}
GET /api/articles/{id}
```

**ML Signals**
```http
GET /api/signals/top-predictions?limit=10&min_score=50
GET /api/signals/predict-tomorrow/{symbol}
GET /api/signals/tickers/{symbol}/score
```

**Intraday Bounds**
```http
GET /api/predict/intraday-bounds/{ticker}?interval=1m&horizon=5
POST /api/predict/intraday-bounds/batch
```

**Analysis & Backtesting**
```http
GET /api/analysis/summary/{ticker}
GET /api/backtest/{ticker}?start_date=2023-01-01
```

**Real-Time Streaming**
```http
GET /api/stream/price/{symbol}     # SSE stream
GET /api/stream/sentiment/{symbol}  # SSE stream
WS /ws/alerts                        # WebSocket
```

**Full documentation:** http://localhost:8000/docs (Swagger UI)

---

## 📁 Project Structure

```
news-tunneler/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── core/               # Core functionality (scoring, sentiment, ML)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── api/                # FastAPI route handlers
│   │   ├── tasks/              # Celery async tasks
│   │   ├── ml/                 # ML pipeline & models
│   │   └── seeds/              # Database seed data
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Unit tests
│   ├── docker-compose.yml      # PostgreSQL + Redis
│   ├── requirements.txt        # Python dependencies
│   └── .env                    # Environment variables
│
├── frontend/                   # SolidJS frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Page components
│   │   └── lib/                # Utilities & state
│   ├── public/                 # Static assets
│   └── package.json            # Node dependencies
│
└── README.md                   # This file
```

---

## 🔧 Configuration

### Backend Environment Variables

**Required:**
```env
OPENAI_API_KEY=sk-...           # OpenAI API key for LLM analysis
```

**Database (SQLite - Development):**
```env
DATABASE_URL=sqlite:///./app.db
USE_POSTGRESQL=false
```

**Database (PostgreSQL - Production):**
```env
USE_POSTGRESQL=true
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

**Redis (Production):**
```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

**Optional Services:**
```env
# Email Digests
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
REPORT_RECIPIENTS=["recipient@example.com"]

# Additional Data Sources
POLYGON_API_KEY=your-polygon-key
NEWSAPI_KEY=your-newsapi-key

# Monitoring
SENTRY_DSN=https://...@sentry.io/project
PROMETHEUS_ENABLED=true

# Scheduler
POLL_INTERVAL_SEC=1800          # RSS polling (30 min)
```

### Frontend Environment Variables

```env
VITE_API_BASE=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/alerts
```

---

## 🧪 Testing

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_scoring.py
```

**Test Coverage:**
- ✅ Scoring algorithm (96/96 tests passing - 96.9%)
- ✅ Article deduplication
- ✅ Ticker extraction
- ✅ API endpoints
- ✅ ML models & feature engineering
- ✅ Celery tasks

---

## 🐛 Troubleshooting

**Backend won't start:**
```bash
# Check Python version
python --version  # Should be 3.12+

# Reinstall dependencies
pip install -r backend/requirements.txt

# Run migrations
cd backend && alembic upgrade head
```

**Database errors:**
```bash
# SQLite: Reset database (WARNING: deletes data)
rm backend/app.db
cd backend && alembic upgrade head

# PostgreSQL: Check connection
docker exec news-tunneler-postgres psql -U news_tunneler -c "\dt"
```

**"OpenAI API key not found":**
```bash
# Add to backend/.env
echo "OPENAI_API_KEY=sk-..." >> backend/.env
```

**"Port 8000 already in use":**
```bash
# Kill process using port
lsof -ti:8000 | xargs kill -9
```

---

## 📈 Performance

- **API Response Time**: <100ms (cached), <500ms (uncached)
- **Feature Access**: <1ms (Redis cache hit)
- **ML Prediction**: <50ms (with feature store)
- **Database Queries**: <10ms (with indexes)
- **RSS Polling**: 20+ feeds in <30 seconds
- **Test Pass Rate**: 96.9% (93/96 tests passing)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

**Core Technologies:** OpenAI, yfinance, FastAPI, SolidJS, Tailwind CSS, ApexCharts

**ML & Data Science:** scikit-learn, XGBoost, LightGBM, Transformers, PyTorch, SHAP

**Infrastructure:** PostgreSQL, Redis, Celery, Docker, Prometheus, Grafana, Sentry

---

## 📧 Contact

**Charles W Boswell**
- GitHub: [@Boswecw](https://github.com/Boswecw)
- Email: charliewboswell@gmail.com
- Project: [News Tunneler](https://github.com/Boswecw/News_Tunneler)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ by [Charles W Boswell](https://github.com/Boswecw)

</div>
