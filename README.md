# 📰 News Tunneler

<div align="center">

![News Tunneler Logo](frontend/public/logo.webp)

**AI-Powered Trading Analytics Platform**

*Combining real-time market data, sentiment analysis, and machine learning to identify high-conviction trading opportunities*

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![SolidJS](https://img.shields.io/badge/SolidJS-1.8+-blue.svg)](https://www.solidjs.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [API Reference](#-api-reference) • [Screenshots](#-screenshots)

</div>

---

## 🎯 Overview

News Tunneler is a comprehensive trading analytics platform that aggregates financial news from 20+ premium sources, analyzes them using advanced machine learning, and provides actionable trading signals with real-time market data visualization.

### What Makes It Unique?

- **🤖 ML-Powered Predictions**: After-hours prediction mode generates next-day trading forecasts based on signal strength and sentiment
- **📊 Real-Time Streaming**: Live price and sentiment charts during market hours (9:30 AM - 4:00 PM ET)
- **🎯 Smart Signals**: Three-tier signal system (High-Conviction, Opportunity, Watch) with confidence scores
- **📈 Backtesting Engine**: Validate strategies against historical data with detailed performance metrics
- **🔍 Multi-Source Intelligence**: Monitors SEC filings, financial news, FDA approvals, energy reports, and more
- **💡 AI Trading Plans**: GPT-4 generated entry/exit strategies with risk management

## ✨ Features

### 🎨 Frontend (SolidJS + TypeScript)

#### **Dashboard**
- Real-time KPIs: Total articles, high-conviction signals, average score, active sources
- Recent alerts feed with live updates via WebSocket
- Quick access to top opportunities and recent analyses

#### **Live Charts**
- **Market Hours Mode**: Real-time streaming price + sentiment charts (updates every minute)
- **After-Hours Mode**: ML-generated predictions for next trading session
- **Buy/Sell Signals**: Predicted optimal entry/exit points on prediction charts
- **Auto-Loading**: Top 5 predicted stocks load automatically
- **Custom Watchlist**: Add any ticker to track

#### **Opportunities**
- Ranked list of stocks with recent ML signals
- Signal labels: High-Conviction (70-100), Opportunity (50-69), Watch (30-49)
- Sentiment analysis with bullish/bearish indicators
- Recent news articles with scores
- AI-generated trading plans with strategy recommendations
- Backtesting results for each opportunity

#### **Alerts**
- Filterable table of all scored articles
- Search by ticker, keyword, or source
- Score breakdown tooltips (Catalyst, Novelty, Credibility, Sentiment, Liquidity)
- Direct links to original articles

#### **Sources**
- Manage 20+ RSS/Atom feeds
- Enable/disable sources individually
- Add custom feeds with automatic parsing
- Source credibility ratings

#### **Settings**
- Adjust scoring weights (Catalyst, Novelty, Credibility, Sentiment, Liquidity)
- Configure alert thresholds
- Email digest settings (morning/evening)
- Dark mode toggle

#### **FAQ**
- Comprehensive documentation
- Category filtering (General, Live Charts, ML & Signals, Data Sources, Features, Technical, Trading)
- 24+ frequently asked questions

### 🚀 Backend (Python + FastAPI)

#### **Core Features**
- **Multi-Source Ingestion**: RSS, Atom feeds from 20+ financial sources
- **Intelligent Scoring**: 5-factor algorithm with configurable weights
- **ML Signal Generation**: Predictive model with confidence scores
- **Real-Time Streaming**: Server-Sent Events (SSE) for price and sentiment data
- **Backtesting Engine**: Historical performance analysis
- **Price Caching**: Efficient data retrieval with SQLite cache
- **Background Jobs**: Automated RSS polling, LLM analysis, email digests
- **API Documentation**: Interactive Swagger/OpenAPI at `/docs`

#### **Data Sources** (20+ Premium Feeds)
- **SEC Filings**: EDGAR RSS (8-K, 10-K, 10-Q, 13F)
- **Financial News**: Financial Times, Reuters, Bloomberg, WSJ, MarketWatch
- **Analysis**: Seeking Alpha, Motley Fool, Benzinga
- **Specialized**: FDA.gov, EIA.gov, Treasury.gov
- **Crypto**: CoinDesk, CoinTelegraph
- **Tech**: TechCrunch, The Verge

#### **API Endpoints**

**Articles & Alerts**
- `GET /api/articles` - List articles with filtering (search, score, ticker, date)
- `GET /api/articles/{id}` - Get article details with score breakdown

**ML Signals**
- `GET /api/signals/top-predictions` - Top predicted stocks (default: 10, min_score: 50)
- `GET /api/signals/predict-tomorrow/{symbol}` - Generate prediction chart for next session
- `GET /api/signals/tickers/{symbol}/score` - Latest ML score for ticker
- `POST /api/signals/recalculate/{symbol}` - Force recalculation of signal

**Analysis & Backtesting**
- `GET /api/analysis/summary/{ticker}` - Technical indicators (SMA, RSI, ATR, volume)
- `GET /api/analysis/event-reaction/{ticker}` - Historical event reactions
- `GET /api/backtest/{ticker}` - Backtest simple strategy (buy on signal, sell at close)

**Real-Time Streaming**
- `GET /api/stream/price/{symbol}` - SSE stream of real-time price data
- `GET /api/stream/sentiment/{symbol}` - SSE stream of sentiment scores
- `WS /ws/alerts` - WebSocket for real-time alerts

**Sources & Settings**
- `GET /api/sources` - List all RSS sources
- `POST /api/sources` - Add new RSS feed
- `PATCH /api/sources/{id}` - Enable/disable source
- `DELETE /api/sources/{id}` - Remove source
- `GET /api/settings` - Get scoring weights and thresholds
- `PATCH /api/settings` - Update configuration

**Admin**
- `POST /api/admin/run-llm-analysis` - Trigger LLM analysis job
- `POST /api/admin/poll-feeds` - Manually poll RSS feeds
- `GET /health` - Health check

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** (for backend)
- **Bun** or **Node.js 18+** (for frontend)
- **OpenAI API Key** (required for LLM analysis)
- **SMTP Credentials** (optional, for email digests)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/Boswecw/News_Tunneler.git
cd News_Tunneler
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key and other settings

# Run database migrations
alembic upgrade head

# Seed initial data (optional)
python -m app.seeds.seed_sources
python -m app.seeds.seed_tickers

# Start backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at **http://localhost:8000**
API documentation at **http://localhost:8000/docs**

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies (using Bun - recommended)
bun install
# Or with npm: npm install

# Start development server
bun run dev
# Or with npm: npm run dev
```

Frontend will be available at **http://localhost:5173**

### Environment Variables

#### Backend (`.env`)

```env
# Required
OPENAI_API_KEY=sk-...                    # OpenAI API key for LLM analysis

# Database
DATABASE_URL=sqlite:///./app.db          # SQLite database path

# Scheduler
POLL_INTERVAL_SEC=1800                   # RSS polling interval (30 min)
LLM_ANALYSIS_CRON=0 0,6,12,18 * * *     # LLM analysis schedule (4x daily)

# Email Digests (Optional)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_TO=recipient@example.com

# Slack (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# API Keys (Optional)
POLYGON_API_KEY=your-polygon-key         # Enhanced market data
NEWSAPI_KEY=your-newsapi-key             # Additional news source

# Server
PORT=8000
DEBUG=true
```

#### Frontend (`.env.local`)

```env
VITE_API_BASE=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/alerts
```

### First Run

1. **Start Backend**: The scheduler will automatically begin polling RSS feeds every 30 minutes
2. **Start Frontend**: Navigate to http://localhost:5173
3. **Check Dashboard**: You should see KPIs and recent articles appearing
4. **Add Tickers to Live Charts**: Go to Live Charts page and add symbols (e.g., AAPL, NVDA, TSLA)
5. **Explore Opportunities**: Check the Opportunities page for ML-generated signals
6. **Configure Settings**: Adjust scoring weights and thresholds in Settings page

## 📁 Project Structure

```
news-tunneler/
├── backend/                           # Python FastAPI backend
│   ├── app/
│   │   ├── core/                      # Core functionality
│   │   │   ├── config.py              # Environment configuration
│   │   │   ├── db.py                  # Database session management
│   │   │   ├── scoring.py             # 5-factor scoring algorithm
│   │   │   ├── sentiment.py           # VADER sentiment analysis
│   │   │   ├── tickers.py             # Ticker extraction & symbol mapping
│   │   │   ├── rss.py                 # RSS/Atom feed parsing
│   │   │   ├── dedupe.py              # Article deduplication
│   │   │   ├── notifiers.py           # Slack/Email notifications
│   │   │   ├── scheduler.py           # APScheduler background jobs
│   │   │   ├── prices.py              # yfinance price data fetching
│   │   │   ├── signals.py             # ML signal generation
│   │   │   ├── backtest.py            # Backtesting engine
│   │   │   └── logging.py             # Structured logging
│   │   ├── models/                    # SQLAlchemy ORM models
│   │   │   ├── source.py              # RSS feed sources
│   │   │   ├── article.py             # News articles
│   │   │   ├── score.py               # Article scores
│   │   │   ├── setting.py             # User settings
│   │   │   ├── webhook.py             # Notification history
│   │   │   ├── price_cache.py         # Cached price data
│   │   │   ├── signal.py              # ML signals
│   │   │   └── model_run.py           # ML model metadata
│   │   ├── api/                       # FastAPI route handlers
│   │   │   ├── articles.py            # Article endpoints
│   │   │   ├── sources.py             # Source management
│   │   │   ├── settings.py            # Settings endpoints
│   │   │   ├── signals.py             # ML signal endpoints
│   │   │   ├── analysis.py            # Technical analysis
│   │   │   ├── backtest.py            # Backtesting endpoints
│   │   │   ├── stream.py              # SSE streaming
│   │   │   ├── websocket.py           # WebSocket alerts
│   │   │   └── admin.py               # Admin operations
│   │   ├── seeds/                     # Database seed data
│   │   │   ├── seed_sources.py        # Initial RSS feeds
│   │   │   └── seed_tickers.py        # Ticker symbol map
│   │   └── main.py                    # FastAPI application
│   ├── alembic/                       # Database migrations
│   ├── tests/                         # Unit tests
│   ├── requirements.txt               # Python dependencies
│   └── .env                           # Environment variables
│
├── frontend/                          # SolidJS frontend
│   ├── src/
│   │   ├── components/                # Reusable UI components
│   │   │   ├── Navigation.tsx         # Top navigation bar
│   │   │   ├── RunningLineChart.tsx   # Live/prediction charts
│   │   │   ├── AlertTable.tsx         # Article alerts table
│   │   │   ├── AnalysisCard.tsx       # Analysis display
│   │   │   ├── BacktestCard.tsx       # Backtest results
│   │   │   ├── PlanDrawer.tsx         # AI trading plan drawer
│   │   │   ├── OpportunitiesPanel.tsx # Opportunities list
│   │   │   ├── Kpis.tsx               # Dashboard KPIs
│   │   │   ├── SourceForm.tsx         # Add source form
│   │   │   └── WeightSliders.tsx      # Scoring weight controls
│   │   ├── pages/                     # Page components
│   │   │   ├── Dashboard.tsx          # Main dashboard
│   │   │   ├── LiveCharts.tsx         # Live charts page
│   │   │   ├── Opportunities.tsx      # Opportunities page
│   │   │   ├── Alerts.tsx             # Alerts page
│   │   │   ├── Sources.tsx            # Source management
│   │   │   ├── Settings.tsx           # Settings page
│   │   │   └── FAQ.tsx                # FAQ page
│   │   ├── lib/                       # Utilities & state
│   │   │   ├── api.ts                 # API client functions
│   │   │   ├── store.ts               # Global state management
│   │   │   ├── ws.ts                  # WebSocket client
│   │   │   ├── analysis.ts            # Analysis utilities
│   │   │   ├── backtest.ts            # Backtest utilities
│   │   │   └── annotations.ts         # Chart annotations
│   │   ├── App.tsx                    # Root component & routing
│   │   ├── main.tsx                   # Application entry point
│   │   └── app.css                    # Global styles
│   ├── public/                        # Static assets
│   │   └── logo.webp                  # Application logo
│   ├── package.json                   # Node dependencies
│   ├── vite.config.ts                 # Vite configuration
│   ├── tailwind.config.js             # Tailwind CSS config
│   └── tsconfig.json                  # TypeScript config
│
├── docs/                              # Documentation
│   ├── ARCHITECTURE.md                # System architecture
│   ├── DEPLOYMENT.md                  # Deployment guide
│   └── EXTENDING.md                   # Extension guide
│
├── docker-compose.yml                 # Docker Compose config
├── Makefile                           # Build automation
└── README.md                          # This file
```

## 🧠 How It Works

### 1. **Data Ingestion**
- APScheduler polls 20+ RSS feeds every 30 minutes
- Articles are parsed, deduplicated (URL + title hash), and stored
- Ticker symbols extracted using regex + symbol mapping (2000+ tickers)

### 2. **Scoring Algorithm**

Each article receives a score from 0-100 based on five weighted factors:

```python
Total Score = (Catalyst × w_catalyst)
            + (Novelty × w_novelty)
            + (Credibility × w_credibility)
            + (Sentiment × w_sentiment)
            + (Liquidity × w_liquidity)
```

**Factor Breakdown:**

| Factor | Range | Description | Examples |
|--------|-------|-------------|----------|
| **Catalyst** | 0-5 | Market-moving potential | Merger, FDA approval, earnings beat, SEC filing |
| **Novelty** | 0-5 | Time-based freshness | 5 if <6h old, 3 if <24h, 1 if older |
| **Credibility** | 0-5 | Source trustworthiness | 5 for WSJ/Bloomberg, 3 for general news, 1 for blogs |
| **Sentiment** | 1-4 | VADER compound score | 4 (very positive) to 1 (very negative) |
| **Liquidity** | 0-5 | Trading volume/ease | Based on average volume (future: real-time API) |

**Default Weights:**
- Catalyst: 3.0
- Novelty: 2.0
- Credibility: 2.5
- Sentiment: 1.5
- Liquidity: 1.0

**Alert Threshold:** Articles scoring ≥12 trigger alerts

### 3. **ML Signal Generation**

Runs 4x daily (12 AM, 6 AM, 12 PM, 6 PM ET):

1. **Feature Extraction**: Aggregates recent articles (7-30 days) per ticker
2. **Sentiment Analysis**: Computes weighted sentiment from article scores
3. **Technical Indicators**: Fetches price data, calculates SMA, RSI, ATR
4. **Signal Scoring**: Combines features into 0-100 score
5. **Labeling**:
   - **High-Conviction** (70-100): Strong buy signals
   - **Opportunity** (50-69): Moderate signals
   - **Watch** (30-49): Weak signals to monitor
6. **Caching**: Stores signals in database and in-memory cache

### 4. **Real-Time Streaming**

**During Market Hours (9:30 AM - 4:00 PM ET):**
- SSE streams price data from yfinance (1-minute intervals)
- Sentiment scores updated from recent articles
- Charts update automatically

**After Hours:**
- Switches to prediction mode
- Generates next-day forecast using latest signal + sentiment
- Shows predicted buy/sell times

### 5. **Backtesting**

For each ticker with signals:
1. Fetches historical daily prices (1 year)
2. Simulates strategy: Buy at open on signal days, sell at close
3. Calculates returns, win rate, max drawdown
4. Displays results with performance metrics

### 6. **AI Trading Plans**

Uses GPT-4 to generate trading plans:
- Analyzes signal strength, sentiment, recent news
- Recommends strategy (Momentum, Swing, DCA, Pairs, Avoid)
- Provides entry/exit levels, position sizing, risk management
- Includes rationale and key risks

## 📚 API Reference

Full interactive documentation available at **http://localhost:8000/docs** (Swagger UI)

### Articles & Alerts

```http
GET /api/articles?q={search}&min_score={score}&ticker={symbol}&limit={n}
```
List articles with filtering. Supports search, score threshold, ticker filter, date range.

**Response:**
```json
[
  {
    "id": 123,
    "title": "Apple Announces Record Earnings",
    "url": "https://...",
    "summary": "...",
    "source_name": "Reuters",
    "published_at": "2024-01-15T10:30:00Z",
    "ticker_guess": "AAPL",
    "score": 85.5
  }
]
```

### ML Signals

```http
GET /api/signals/top-predictions?limit=10&min_score=50&days=30
```
Get top predicted stocks based on recent signals.

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "score": 75.3,
    "label": "High-Conviction",
    "predicted_return": 0.045,
    "confidence": 0.85,
    "t": 1705320000000,
    "article_id": 123
  }
]
```

```http
GET /api/signals/predict-tomorrow/{symbol}
```
Generate prediction chart for next trading session.

**Response:**
```json
{
  "symbol": "AAPL",
  "data": [
    {"t": 1705320600000, "price": 185.23},
    {"t": 1705320900000, "price": 185.45},
    ...
  ],
  "buy_signal": {"t": 1705323000000, "price": 184.50},
  "sell_signal": {"t": 1705334400000, "price": 186.75},
  "predicted_return": 0.0122,
  "market_open": 1705320600000,
  "market_close": 1705343400000
}
```

### Analysis & Backtesting

```http
GET /api/analysis/summary/{ticker}
```
Get technical indicators and current price summary.

**Response:**
```json
{
  "ticker": "AAPL",
  "current_price": 185.50,
  "sma_20": 183.25,
  "sma_50": 180.10,
  "rsi_14": 62.5,
  "atr_14": 3.25,
  "volume": 52000000,
  "week_52_high": 198.23,
  "week_52_low": 164.08
}
```

```http
GET /api/backtest/{ticker}?start_date=2023-01-01&end_date=2024-01-01
```
Backtest simple strategy (buy on signal days, sell at close).

**Response:**
```json
{
  "ticker": "AAPL",
  "total_return": 0.234,
  "num_trades": 12,
  "win_rate": 0.667,
  "avg_return": 0.0195,
  "max_drawdown": -0.085,
  "sharpe_ratio": 1.45,
  "trades": [...]
}
```

### Real-Time Streaming

```http
GET /api/stream/price/{symbol}
```
Server-Sent Events stream of real-time price data (1-minute intervals during market hours).

```http
GET /api/stream/sentiment/{symbol}
```
Server-Sent Events stream of sentiment scores from recent articles.

### WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/alerts');
ws.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  console.log('New alert:', alert);
};
```

Receives real-time alerts when new high-scoring articles are published.

## 🗄️ Database Schema

**SQLite** with **SQLAlchemy ORM** and **Alembic** migrations.

### Models

| Model | Description | Key Fields |
|-------|-------------|------------|
| **Source** | RSS/Atom feeds | `url`, `name`, `type`, `enabled`, `credibility` |
| **Article** | News articles | `url`, `title`, `summary`, `published_at`, `ticker_guess` |
| **Score** | Article scores | `article_id`, `catalyst`, `novelty`, `credibility`, `sentiment`, `liquidity`, `total` |
| **Signal** | ML signals | `symbol`, `score`, `label`, `predicted_return`, `confidence`, `features` |
| **PriceCache** | Cached prices | `symbol`, `date`, `open`, `high`, `low`, `close`, `volume` |
| **Setting** | User settings | `weights`, `thresholds`, `email_config` |
| **Webhook** | Notifications | `type`, `url`, `last_sent_at` |
| **ModelRun** | ML metadata | `run_id`, `model_version`, `metrics`, `created_at` |

### Migrations

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_scoring.py

# Run with coverage
pytest --cov=app --cov-report=html
```

**Test Coverage:**
- ✅ Scoring algorithm (all 5 factors)
- ✅ Article deduplication
- ✅ Ticker extraction
- ✅ API endpoints (articles, sources, settings)
- ✅ Sentiment analysis
- ✅ RSS feed parsing

### Frontend Tests

```bash
cd frontend

# Run tests (if configured)
bun test
```

## 🚢 Deployment

### Option 1: Docker Compose (Recommended)

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access at **http://localhost:5173**

### Option 2: Manual Deployment

#### Backend (Production)

```bash
cd backend
source venv/bin/activate

# Install production dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### Frontend (Production)

```bash
cd frontend

# Build for production
bun run build

# Preview build
bun run preview

# Or serve with nginx/caddy
# Copy dist/ folder to web server
```

### Option 3: Cloud Deployment

**Backend (Railway, Render, Fly.io):**
1. Connect GitHub repo
2. Set environment variables
3. Deploy from `backend/` directory
4. Run migrations on first deploy

**Frontend (Vercel, Netlify, Cloudflare Pages):**
1. Connect GitHub repo
2. Set build command: `cd frontend && bun run build`
3. Set output directory: `frontend/dist`
4. Set environment variables (VITE_API_BASE)

## 🛠️ Development

### Tech Stack

**Backend:**
- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0
- **Database**: SQLite (production: PostgreSQL recommended)
- **Async**: asyncio + httpx
- **Scheduler**: APScheduler
- **ML/AI**: OpenAI GPT-4, scikit-learn
- **Data**: pandas, yfinance
- **Testing**: pytest

**Frontend:**
- **Framework**: SolidJS 1.8+
- **Language**: TypeScript 5.0+
- **Build**: Vite 5.0+
- **Styling**: Tailwind CSS 3.4+
- **Charts**: ApexCharts
- **State**: SolidJS signals (reactive)
- **HTTP**: Fetch API

### Code Style

**Backend:**
```bash
# Format with black
black app/

# Lint with ruff
ruff check app/

# Type check with mypy
mypy app/
```

**Frontend:**
```bash
# Format with prettier
bun run format

# Lint with eslint
bun run lint
```

## 🎨 Screenshots

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)
*Real-time KPIs, recent alerts, and quick access to opportunities*

### Live Charts
![Live Charts](docs/screenshots/live-charts.png)
*Real-time price and sentiment streaming during market hours*

### Prediction Mode
![Prediction Mode](docs/screenshots/prediction.png)
*After-hours ML predictions with buy/sell signals*

### Opportunities
![Opportunities](docs/screenshots/opportunities.png)
*Ranked signals with AI-generated trading plans*

### Backtesting
![Backtesting](docs/screenshots/backtest.png)
*Historical performance analysis with detailed metrics*

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Write tests for new features
- Follow existing code style
- Update documentation
- Add type hints (Python) / types (TypeScript)
- Keep commits atomic and well-described

## 🐛 Troubleshooting

### Backend Issues

**Backend won't start**
```bash
# Check Python version
python --version  # Should be 3.12+

# Reinstall dependencies
pip install -r backend/requirements.txt

# Run migrations
cd backend && alembic upgrade head

# Check logs
tail -f backend/app.log
```

**Database errors**
```bash
# Reset database (WARNING: deletes all data)
rm backend/app.db
alembic upgrade head

# Or create backup first
cp backend/app.db backend/app.db.backup
```

**RSS feeds not polling**
```bash
# Check scheduler is running
curl http://localhost:8000/health

# Manually trigger poll
curl -X POST http://localhost:8000/api/admin/poll-feeds

# Check logs for errors
grep "RSS" backend/app.log
```

### Frontend Issues

**Frontend won't connect to backend**
```bash
# Check API is running
curl http://localhost:8000/health

# Verify environment variables
cat frontend/.env.local

# Check CORS settings in backend
# Should allow http://localhost:5173
```

**WebSocket connection fails**
- Ensure backend is running on port 8000
- Check `VITE_WS_URL` in `frontend/.env.local`
- Open browser console and check for errors
- Verify firewall isn't blocking WebSocket connections

**Charts not loading**
- Check browser console for errors
- Verify ticker symbol is valid
- Ensure yfinance can fetch data for the symbol
- Check if market is open (for live mode)

### Common Errors

**"No module named 'app'"**
```bash
# Make sure you're in the backend directory
cd backend
# And virtual environment is activated
source venv/bin/activate
```

**"OpenAI API key not found"**
```bash
# Add to backend/.env
echo "OPENAI_API_KEY=sk-..." >> backend/.env
```

**"Port 8000 already in use"**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
```

## 📖 Documentation

- **[Architecture](docs/ARCHITECTURE.md)**: System design and data flow
- **[Deployment](docs/DEPLOYMENT.md)**: Production deployment guide
- **[Extending](docs/EXTENDING.md)**: How to add new features
- **[FAQ](http://localhost:5173/faq)**: Frequently asked questions (in-app)

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** - GPT-4 for LLM analysis
- **yfinance** - Free market data
- **FastAPI** - Modern Python web framework
- **SolidJS** - Reactive UI framework
- **Tailwind CSS** - Utility-first CSS
- **ApexCharts** - Beautiful charts

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

