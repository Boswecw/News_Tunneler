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
- **Intraday Bounds Prediction**: ML-powered high/low bounds for 5/15/30-minute horizons
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

---

## 🚀 Advanced ML Features (Phase 3, 4 & 5)

### **Phase 5: Intraday Bounds Prediction** ✅

#### **1. ML-Powered High/Low Prediction**
- **Quantile Regression Models**: XGBoost/LightGBM with quantile loss (q10, q90)
- **Multiple Horizons**: 5-minute, 15-minute, 30-minute ahead predictions
- **Real-Time Updates**: Bounds refresh every minute during market hours
- **No-Look-Ahead Guarantee**: Features at time t only use data from indices ≤ t
- **Walk-Forward Validation**: Time-based train/test split (no random shuffle)

#### **2. Feature Engineering (30+ Intraday Features)**
- **Price Features**: Returns, volatility, range, gaps, normalized price
- **Volume Features**: Volume ratio, VWAP distance, volume momentum
- **Technical Indicators**: RSI, MACD, Bollinger Bands, ATR, momentum
- **Temporal Features**: Time of day, market session, normalized time
- **Microstructure**: Bid-ask spread proxies, price acceleration

#### **3. Training & Backtesting**
- **Training CLI**: `python -m app.ml.train_intraday_bounds --ticker AAPL --interval 1m --horizons 5 15 --days 7`
- **Backtest CLI**: `python -m app.ml.backtest_bounds --ticker AAPL --interval 1m --horizon 5`
- **Performance Metrics**: Coverage rate, band width, pinball loss, MAE
- **Model Persistence**: Joblib serialization with versioning

#### **4. API Integration**
- **Prediction Endpoint**: `GET /predict/intraday-bounds/{ticker}?interval=1m&horizon=5&limit=200`
- **Batch Predictions**: `POST /predict/intraday-bounds/batch`
- **Database Storage**: SQLAlchemy model for caching predictions
- **Scheduler Integration**: Automatic bounds refresh during market hours

#### **5. Frontend Visualization**
- **Shaded Area Bands**: Indigo-colored confidence intervals on charts
- **Toggle Controls**: Enable/disable bounds overlay
- **Horizon Selector**: Switch between 5m, 15m, 30m predictions
- **Enhanced Tooltip**: Shows current price, bounds, and band width percentage

### **Phase 3: ML Enhancements** ✅

#### **1. Advanced ML Models**
- **4 Model Types**: Random Forest, XGBoost, LightGBM, Gradient Boosting
- **Hyperparameter Tuning**: GridSearchCV with cross-validation
- **Model Comparison**: Automatic best model selection
- **Feature Importance**: SHAP-based explainability
- **Model Versioning**: Track and compare model versions
- **Persistence**: Save/load models with metadata

#### **2. Feature Engineering (30+ Features)**
- **Technical Indicators**: RSI, MACD, Bollinger Bands, ATR, Stochastic, ADX, CCI, Williams %R, OBV, MFI
- **Sentiment Aggregation**: Weighted sentiment, magnitude, credibility scores
- **Temporal Features**: Day of week, hour, market hours, pre/after market, weekend flags
- **Interaction Features**: Sentiment×volatility, sentiment×momentum, novelty×credibility, RSI×sentiment, MACD×sentiment, volatility×gap

#### **3. FinBERT Sentiment Analysis**
- **Financial-Specific**: ProsusAI/finbert model (438MB)
- **VADER Fallback**: Graceful degradation if FinBERT fails
- **Batch Processing**: Efficient sentiment updates via Celery
- **Caching**: Redis-based sentiment caching

#### **4. Model Explainability**
- **SHAP Values**: Feature importance for individual predictions
- **Global Importance**: Aggregate feature importance across all predictions
- **Prediction Explanations**: Top contributing features for each signal
- **Visualization Ready**: SHAP values formatted for charts

#### **5. Training Pipeline**
- **End-to-End**: Data extraction → Feature engineering → Training → Evaluation → Persistence
- **Configurable**: Model types, hyperparameters, feature engineering toggles
- **Metrics Tracking**: Accuracy, precision, recall, F1, ROC-AUC
- **Database Integration**: Store models with metadata in PostgreSQL

### **Phase 4: Production Integration** ✅

#### **1. Celery ML Tasks**
- **5 Async Tasks**:
  - `train_ml_model_task` - Async model training with configurable parameters
  - `batch_predict_task` - Batch predictions for multiple signals
  - `update_sentiment_task` - Update sentiment using FinBERT
  - `scheduled_retrain_task` - Daily automated retraining (2 AM UTC)
  - `evaluate_model_task` - Model performance evaluation
- **Custom Error Handling**: MLTask base class with retry logic
- **Queue Routing**: ML tasks routed to LLM queue
- **Scheduled Jobs**: Daily retraining via Celery Beat

#### **2. Model Monitoring**
- **Real-Time Metrics**: Accuracy, precision, recall, F1 on recent predictions
- **Drift Detection**: Kolmogorov-Smirnov test for feature distribution changes
- **Confidence Tracking**: Monitor prediction confidence trends over time
- **Health Checks**: Automated warnings for model degradation
- **API Endpoints**: 4 monitoring endpoints for observability

#### **3. A/B Testing Framework**
- **Traffic Splitting**: Consistent hash-based assignment (50/50 or custom)
- **Statistical Testing**: Two-proportion z-test for significance
- **Performance Comparison**: Side-by-side model metrics
- **Winner Selection**: Automated recommendation based on p-value
- **Traffic Distribution**: Track actual vs expected split

#### **4. Feature Store**
- **Redis Caching**: Sub-millisecond feature access (100x faster)
- **TTL-Based Expiration**: 1h for most features, 24h for temporal
- **Batch Retrieval**: Efficient multi-symbol feature generation
- **Feature Versioning**: Support multiple feature versions
- **Cache Statistics**: Monitor cache hit rates and usage

#### **5. ML-Enhanced Signal Scoring**
- **Automatic Enhancement**: Add 30+ engineered features to base signals
- **Configurable Weight**: ML prediction weight (default: 30%)
- **Graceful Fallback**: Traditional scoring if ML disabled
- **Feature Flags**: Gradual rollout control
- **Metadata Tracking**: ML boost, base score, prediction confidence

### 🚀 Backend (Python + FastAPI)

#### **Core Features**
- **Multi-Source Ingestion**: RSS, Atom feeds from 20+ financial sources
- **Intelligent Scoring**: 5-factor algorithm with configurable weights
- **Advanced ML Pipeline**: Random Forest, XGBoost, LightGBM with feature engineering
- **Real-Time Streaming**: Server-Sent Events (SSE) for price and sentiment data
- **Backtesting Engine**: Historical performance analysis
- **PostgreSQL + Redis**: Production-ready database with caching layer
- **Celery Task Queue**: Async processing for ML, LLM, and RSS tasks
- **Feature Flags**: Gradual rollout control for new features
- **Structured Logging**: JSON logs with request tracking
- **API Documentation**: Interactive Swagger/OpenAPI at `/docs`

#### **Infrastructure (Phase 2)**
- **PostgreSQL 16**: Production database with connection pooling
- **Redis**: Caching layer + Celery broker
- **Celery + Beat**: Distributed task queue with scheduling
- **Docker Compose**: PostgreSQL, Redis, PgAdmin containers
- **Alembic Migrations**: Database version control
- **Request ID Tracking**: Distributed tracing support
- **JSON Logging**: Structured logs for aggregation (ELK, Datadog)
- **Feature Flag System**: 18 flags across 5 categories

#### **Data Sources** (20+ Premium Feeds)
- **SEC Filings**: EDGAR RSS (8-K, 10-K, 10-Q, 13F)
- **Financial News**: Financial Times, Reuters, Bloomberg, WSJ, MarketWatch
- **Analysis**: Seeking Alpha, Motley Fool, Benzinga
- **Specialized**: FDA.gov, EIA.gov, Treasury.gov
- **Crypto**: CoinDesk, CoinTelegraph
- **Tech**: TechCrunch, The Verge

---

## 🛠️ Tech Stack

### **Backend**
- **Framework**: FastAPI 0.104+ (Python 3.12+)
- **Database**: PostgreSQL 16 / SQLite 3
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Caching**: Redis 7.0+
- **Task Queue**: Celery 5.3+ with Redis broker
- **Scheduler**: Celery Beat + APScheduler
- **ML Libraries**:
  - scikit-learn 1.3+ (Random Forest, Gradient Boosting)
  - XGBoost 3.1+ (Gradient boosting)
  - LightGBM 4.6+ (Light gradient boosting)
  - Transformers 4.57+ (FinBERT)
  - PyTorch 2.9+ (Deep learning backend)
  - SHAP 0.49+ (Model explainability)
  - TA-Lib 0.11+ (Technical analysis)
- **Data Sources**:
  - yfinance (Stock prices)
  - OpenAI GPT-4 (LLM analysis)
  - feedparser (RSS/Atom parsing)
- **Sentiment**: VADER, FinBERT (ProsusAI/finbert)
- **Testing**: pytest, pytest-asyncio
- **Logging**: structlog (JSON logging)

### **Frontend**
- **Framework**: SolidJS 1.8+
- **Language**: TypeScript 5.0+
- **Build Tool**: Vite 5.0+
- **Styling**: Tailwind CSS 3.4+
- **Charts**: ApexCharts 3.45+
- **HTTP Client**: Axios
- **State Management**: SolidJS stores
- **Real-Time**: WebSocket, Server-Sent Events (SSE)

### **Infrastructure**
- **Containerization**: Docker, Docker Compose
- **Database Admin**: PgAdmin 4
- **Task Monitoring**: Flower (Celery)
- **Version Control**: Git, GitHub

#### **API Endpoints**

**Articles & Alerts**
- `GET /api/articles` - List articles with filtering (search, score, ticker, date)
- `GET /api/articles/{id}` - Get article details with score breakdown

**ML Signals**
- `GET /api/signals/top-predictions` - Top predicted stocks (default: 10, min_score: 50)
- `GET /api/signals/predict-tomorrow/{symbol}` - Generate prediction chart for next session
- `GET /api/signals/tickers/{symbol}/score` - Latest ML score for ticker
- `POST /api/signals/recalculate/{symbol}` - Force recalculation of signal
- `GET /api/signals/ml-status` - Get ML system status (models, features, caching)

**Intraday Bounds Prediction (Phase 5)**
- `GET /predict/intraday-bounds/{ticker}` - Get intraday high/low bounds predictions
- `POST /predict/intraday-bounds/batch` - Batch bounds predictions for multiple tickers
- `GET /predict/intraday-bounds/db/{ticker}` - Get cached bounds from database

**Advanced ML (Phase 3 & 4)**
- `POST /api/ml/train` - Train ML models with feature engineering
- `POST /api/ml/predict` - Get ML prediction for features
- `GET /api/ml/models` - List all trained models
- `GET /api/ml/models/{version}` - Get model details
- `POST /api/ml/models/{version}/activate` - Activate model version
- `DELETE /api/ml/models/{version}` - Delete model
- `GET /api/ml/monitor/accuracy` - Get model accuracy metrics
- `GET /api/ml/monitor/drift` - Get feature drift detection results
- `GET /api/ml/monitor/confidence-trend` - Get prediction confidence trend
- `GET /api/ml/monitor/summary` - Get comprehensive performance summary
- `POST /api/ml/ab-test/compare` - Compare two models in A/B test
- `POST /api/ml/ab-test/traffic` - Get A/B test traffic distribution

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

**Feature Flags**
- `GET /api/feature-flags` - List all feature flags
- `POST /api/feature-flags/{flag}/enable` - Enable feature flag
- `POST /api/feature-flags/{flag}/disable` - Disable feature flag

**Admin**
- `POST /api/admin/run-llm-analysis` - Trigger LLM analysis job
- `POST /api/admin/poll-feeds` - Manually poll RSS feeds
- `GET /health` - Health check

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** (for backend)
- **Bun** or **Node.js 18+** (for frontend)
- **Docker** (optional, for PostgreSQL + Redis)
- **OpenAI API Key** (required for LLM analysis)
- **SMTP Credentials** (optional, for email digests)

### System Requirements

**Minimum:**
- 4 GB RAM
- 2 CPU cores
- 10 GB disk space

**Recommended (with ML):**
- 8 GB RAM
- 4 CPU cores
- 20 GB disk space
- GPU (optional, for FinBERT acceleration)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/Boswecw/News_Tunneler.git
cd News_Tunneler
```

#### 2. Backend Setup

##### Option A: SQLite (Quick Start)

```bash
cd backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key

# Run database migrations
alembic upgrade head

# Seed initial data (optional)
python -m app.seeds.seed_sources
python -m app.seeds.seed_tickers

# Start backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

##### Option B: PostgreSQL + Redis (Production)

```bash
cd backend

# Start PostgreSQL and Redis with Docker
docker-compose up -d

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set:
# USE_POSTGRESQL=true
# DATABASE_URL=postgresql://news_tunneler:password@localhost:5432/news_tunneler
# REDIS_HOST=localhost
# REDIS_PORT=6379
# OPENAI_API_KEY=sk-...

# Run database migrations
USE_POSTGRESQL=true alembic upgrade head

# Seed initial data
python -m app.seeds.seed_sources
python -m app.seeds.seed_tickers

# Start Celery worker (in separate terminal)
celery -A app.core.celery_app worker --loglevel=info -Q llm,rss,digest

# Start Celery Beat scheduler (in separate terminal)
celery -A app.core.celery_app beat --loglevel=info

# Start backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at **http://localhost:8000**
API documentation at **http://localhost:8000/docs**
PgAdmin (if using Docker): **http://localhost:5050** (admin@admin.com / admin)

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

# Database (SQLite)
DATABASE_URL=sqlite:///./app.db          # SQLite database path
USE_POSTGRESQL=false                     # Set to true for PostgreSQL

# Database (PostgreSQL - Production)
# USE_POSTGRESQL=true
# DATABASE_URL=postgresql://news_tunneler:password@localhost:5432/news_tunneler
# DB_POOL_SIZE=20
# DB_MAX_OVERFLOW=10

# Redis (Production)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=                          # Optional

# Celery (Production)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

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

# ML Configuration
ML_MODEL_PATH=./ml_models                # Path to store trained models
FINBERT_MODEL=ProsusAI/finbert          # FinBERT model name
USE_GPU=false                            # Enable GPU for FinBERT

# Feature Flags (Optional - defaults in code)
FEATURE_ML_PREDICTIONS=true
FEATURE_ADVANCED_ML=false
FEATURE_FINBERT_SENTIMENT=false
FEATURE_CELERY_TASKS=true

# Server
PORT=8000
DEBUG=true
LOG_LEVEL=INFO
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

### Training ML Models (Optional)

If you want to use advanced ML features:

```bash
cd backend
source venv/bin/activate

# Run Phase 3 ML setup (one-time)
python test_phase3_ml.py

# This will:
# 1. Train Random Forest, XGBoost, LightGBM models
# 2. Generate 30+ engineered features
# 3. Create ml_models table in database
# 4. Save best model as active

# Enable ML features via feature flags
curl -X POST http://localhost:8000/api/feature-flags/advanced_ml/enable
curl -X POST http://localhost:8000/api/feature-flags/finbert_sentiment/enable

# Check ML status
curl http://localhost:8000/api/signals/ml-status
```

### Running Celery Tasks (Production)

For async processing and scheduled jobs:

```bash
# Terminal 1: Celery Worker
celery -A app.core.celery_app worker --loglevel=info -Q llm,rss,digest

# Terminal 2: Celery Beat (Scheduler)
celery -A app.core.celery_app beat --loglevel=info

# Terminal 3: Flower (Monitoring - Optional)
celery -A app.core.celery_app flower --port=5555

# Access Flower dashboard at http://localhost:5555
```

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
│   │   │   ├── sentiment_advanced.py  # FinBERT sentiment (Phase 3)
│   │   │   ├── tickers.py             # Ticker extraction & symbol mapping
│   │   │   ├── rss.py                 # RSS/Atom feed parsing
│   │   │   ├── dedupe.py              # Article deduplication
│   │   │   ├── notifiers.py           # Slack/Email notifications
│   │   │   ├── scheduler.py           # APScheduler background jobs
│   │   │   ├── prices.py              # yfinance price data fetching
│   │   │   ├── signals.py             # ML signal generation
│   │   │   ├── backtest.py            # Backtesting engine
│   │   │   ├── logging.py             # Structured logging (Phase 2)
│   │   │   ├── structured_logging.py  # JSON log formatter (Phase 2)
│   │   │   ├── feature_flags.py       # Feature flag system (Phase 2)
│   │   │   ├── celery_app.py          # Celery configuration (Phase 2)
│   │   │   └── cache.py               # Redis caching utilities (Phase 1)
│   │   ├── middleware/                # FastAPI middleware
│   │   │   ├── rate_limit.py          # Rate limiting (Phase 1)
│   │   │   └── request_id.py          # Request ID tracking (Phase 2)
│   │   ├── models/                    # SQLAlchemy ORM models
│   │   │   ├── source.py              # RSS feed sources
│   │   │   ├── article.py             # News articles
│   │   │   ├── score.py               # Article scores
│   │   │   ├── setting.py             # User settings
│   │   │   ├── webhook.py             # Notification history
│   │   │   ├── price_cache.py         # Cached price data
│   │   │   ├── signal.py              # ML signals
│   │   │   ├── model_run.py           # ML model metadata
│   │   │   └── ml_model.py            # ML model versioning (Phase 3)
│   │   ├── ml/                        # ML pipeline (Phase 3 & 4)
│   │   │   ├── __init__.py
│   │   │   ├── advanced_models.py     # Random Forest, XGBoost, LightGBM
│   │   │   ├── feature_engineering.py # 30+ engineered features
│   │   │   ├── explainability.py      # SHAP-based explanations
│   │   │   ├── training_pipeline.py   # End-to-end training
│   │   │   ├── monitoring.py          # Model monitoring (Phase 4)
│   │   │   ├── ab_testing.py          # A/B testing framework (Phase 4)
│   │   │   ├── feature_store.py       # Redis feature caching (Phase 4)
│   │   │   └── signal_scoring.py      # ML-enhanced scoring (Phase 4)
│   │   ├── tasks/                     # Celery tasks (Phase 2 & 4)
│   │   │   ├── llm_tasks.py           # LLM analysis tasks
│   │   │   ├── rss_tasks.py           # RSS polling tasks
│   │   │   ├── digest_tasks.py        # Email digest tasks
│   │   │   └── ml_tasks.py            # ML training/prediction tasks (Phase 4)
│   │   ├── api/                       # FastAPI route handlers
│   │   │   ├── articles.py            # Article endpoints
│   │   │   ├── sources.py             # Source management
│   │   │   ├── settings.py            # Settings endpoints
│   │   │   ├── signals.py             # ML signal endpoints
│   │   │   ├── ml.py                  # Advanced ML endpoints (Phase 3 & 4)
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
│   │   └── versions/                  # Migration files
│   │       └── 0a1fd3096f0b_add_ml_models_table.py  # Phase 3
│   ├── tests/                         # Unit tests
│   ├── test_phase3_ml.py              # Phase 3 ML tests
│   ├── test_phase4.py                 # Phase 4 integration tests
│   ├── ml_models/                     # Trained ML models (gitignored)
│   ├── docker-compose.yml             # PostgreSQL + Redis + PgAdmin
│   ├── init-db.sql                    # PostgreSQL initialization
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
- **Celery Tasks (Phase 2)**: Async RSS polling with retry logic
- Articles are parsed, deduplicated (URL + title hash), and stored in PostgreSQL/SQLite
- Ticker symbols extracted using regex + symbol mapping (2000+ tickers)
- **Redis Caching (Phase 1)**: Sub-second response times for frequently accessed data

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
| **Sentiment** | 1-4 | VADER/FinBERT sentiment | 4 (very positive) to 1 (very negative) |
| **Liquidity** | 0-5 | Trading volume/ease | Based on average volume (future: real-time API) |

**Default Weights:**
- Catalyst: 3.0
- Novelty: 2.0
- Credibility: 2.5
- Sentiment: 1.5
- Liquidity: 1.0

**Alert Threshold:** Articles scoring ≥12 trigger alerts

### 3. **ML Signal Generation**

#### **Basic ML (Phase 1)**
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

#### **Advanced ML (Phase 3 & 4)**

**Model Training:**
- **4 Model Types**: Random Forest, XGBoost, LightGBM, Gradient Boosting
- **Hyperparameter Tuning**: GridSearchCV with 5-fold cross-validation
- **Model Comparison**: Automatic best model selection based on accuracy
- **Versioning**: Track and compare model versions in PostgreSQL

**Feature Engineering (30+ Features):**
- **Technical Indicators**: RSI, MACD, Bollinger Bands, ATR, Stochastic, ADX, CCI, Williams %R, OBV, MFI
- **Sentiment Aggregation**: Weighted sentiment, magnitude, credibility scores
- **Temporal Features**: Day of week, hour, market hours, pre/after market, weekend flags
- **Interaction Features**: Sentiment×volatility, sentiment×momentum, novelty×credibility, RSI×sentiment, MACD×sentiment, volatility×gap

**FinBERT Sentiment (Phase 3):**
- Financial-specific sentiment using ProsusAI/finbert model (438MB)
- VADER fallback for graceful degradation
- Batch processing via Celery tasks
- Redis caching for sentiment results

**Model Explainability:**
- SHAP values for feature importance
- Top contributing features for each prediction
- Global feature importance across all predictions

**Production Features (Phase 4):**
- **Model Monitoring**: Real-time accuracy tracking, drift detection (KS test), confidence trends
- **A/B Testing**: Compare model versions with statistical significance testing
- **Feature Store**: Redis-based caching for sub-millisecond feature access (100x faster)
- **ML-Enhanced Scoring**: Combine traditional scoring with ML predictions (configurable weight: 30%)
- **Scheduled Retraining**: Daily automated model updates (2 AM UTC via Celery Beat)
- **Celery ML Tasks**: Async training, batch prediction, sentiment updates, model evaluation

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
- **Celery Tasks (Phase 2)**: Async LLM analysis with rate limiting

### 7. **Production Infrastructure (Phase 2)**

**PostgreSQL + Redis:**
- PostgreSQL 16 with connection pooling (20 connections, 10 overflow)
- 9 PostgreSQL-specific indexes (GIN, trigram, partial)
- Redis caching layer + Celery broker
- Docker Compose for one-command setup

**Celery Task Queue:**
- 3 queues: LLM, RSS, Digest
- 9 custom tasks across all queues
- Scheduled tasks with Celery Beat
- Retry logic and error handling

**Structured Logging:**
- JSON log formatter with custom fields
- Request ID tracking via context variables
- Separate log files for different components
- Ready for aggregation (ELK, Datadog)

**Feature Flags:**
- 18 predefined flags across 5 categories
- FeatureFlagManager for runtime control
- Admin API endpoints for toggling
- Gradual rollout support

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

**PostgreSQL 16** (production) or **SQLite** (development) with **SQLAlchemy 2.0 ORM** and **Alembic** migrations.

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
| **MLModel** (Phase 3) | Trained models | `version`, `model_type`, `accuracy`, `is_active`, `model_data`, `feature_importance` |

### PostgreSQL-Specific Optimizations (Phase 2)

**9 Specialized Indexes:**
- GIN index on `articles.title` for full-text search
- GIN trigram index on `articles.summary` for fuzzy search
- Partial index on `articles.ticker_guess` (non-null only)
- Composite index on `(ticker_guess, published_at DESC)`
- Composite index on `(score.total DESC, created_at DESC)`
- Index on `signals.symbol` with `score DESC`
- Index on `price_cache.symbol` with `date DESC`
- Index on `sources.enabled` (partial, true only)
- Index on `ml_models.is_active` (partial, true only)

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
- ✅ API endpoints (articles, sources, settings, signals, ML)
- ✅ Sentiment analysis (VADER, FinBERT)
- ✅ RSS feed parsing
- ✅ **Phase 3 ML Tests** (5/5 passing):
  - Advanced ML models (Random Forest, XGBoost, LightGBM)
  - Feature engineering (30+ features)
  - FinBERT sentiment analysis
  - Model explainability (SHAP)
  - Training pipeline
- ✅ **Phase 4 Integration Tests** (5/5 passing):
  - Model monitoring (accuracy, drift, confidence)
  - A/B testing framework
  - Feature store (Redis caching)
  - ML-enhanced signal scoring
  - Celery ML tasks

### Frontend Tests

```bash
cd frontend

# Run tests (if configured)
bun test
```

## 🚢 Deployment

### Option 1: Docker Compose (Recommended)

**Full Stack with PostgreSQL + Redis:**

```bash
cd backend

# Start infrastructure (PostgreSQL, Redis, PgAdmin)
docker-compose up -d

# Run migrations
USE_POSTGRESQL=true alembic upgrade head

# Start Celery worker (separate terminal)
celery -A app.core.celery_app worker --loglevel=info -Q llm,rss,digest

# Start Celery Beat (separate terminal)
celery -A app.core.celery_app beat --loglevel=info

# Start backend (separate terminal)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start frontend (separate terminal)
cd ../frontend
bun run dev
```

**Services:**
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- PgAdmin: http://localhost:5050 (admin@admin.com / admin)
- Flower (Celery monitoring): http://localhost:5555 (if started)

### Option 2: Manual Deployment

#### Backend (Production)

```bash
cd backend
source venv/bin/activate

# Install production dependencies
pip install -r requirements.txt

# Set environment variables
export USE_POSTGRESQL=true
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
export REDIS_HOST=your-redis-host
export OPENAI_API_KEY=sk-...

# Run migrations
USE_POSTGRESQL=true alembic upgrade head

# Start Celery worker (background or separate process manager)
celery -A app.core.celery_app worker --loglevel=info -Q llm,rss,digest -D

# Start Celery Beat (background or separate process manager)
celery -A app.core.celery_app beat --loglevel=info -D

# Start with Gunicorn (4 workers)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# Or use systemd/supervisor for process management
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
# SQLite: Reset database (WARNING: deletes all data)
rm backend/app.db
cd backend && alembic upgrade head

# SQLite: Or create backup first
cp backend/app.db backend/app.db.backup

# PostgreSQL: Check connection
docker exec news-tunneler-postgres psql -U news_tunneler -d news_tunneler -c "\dt"

# PostgreSQL: Reset database (WARNING: deletes all data)
docker exec news-tunneler-postgres psql -U news_tunneler -d news_tunneler -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
cd backend && USE_POSTGRESQL=true alembic upgrade head
```

**Redis connection errors**
```bash
# Check Redis is running
docker ps | grep redis

# Test Redis connection
redis-cli -h localhost -p 6379 ping

# Restart Redis
docker-compose restart redis

# Check Redis logs
docker logs news-tunneler-redis
```

**Celery tasks not running**
```bash
# Check Celery worker is running
ps aux | grep celery

# Check Celery logs
celery -A app.core.celery_app inspect active

# Restart Celery worker
pkill -f "celery worker"
celery -A app.core.celery_app worker --loglevel=info -Q llm,rss,digest

# Check Celery Beat scheduler
celery -A app.core.celery_app inspect scheduled

# Monitor with Flower
celery -A app.core.celery_app flower --port=5555
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

**ML models not loading / FinBERT errors**
```bash
# Check if models directory exists
ls -la backend/ml_models/

# Re-download FinBERT model
python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; AutoTokenizer.from_pretrained('ProsusAI/finbert'); AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert')"

# Check GPU availability (optional)
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Disable FinBERT if causing issues
curl -X POST http://localhost:8000/api/feature-flags/finbert_sentiment/disable
```

**Feature engineering / ML prediction errors**
```bash
# Check ML system status
curl http://localhost:8000/api/signals/ml-status

# Retrain models
curl -X POST http://localhost:8000/api/ml/train

# Check active model
curl http://localhost:8000/api/ml/models | jq '.[] | select(.is_active==true)'

# Clear feature cache
redis-cli -h localhost -p 6379 FLUSHDB
```

**"Port 8000 already in use"**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
```

## 📊 Performance Metrics

### **Phase 1: Quick Wins** ✅
- **Redis Caching**: 100x faster response times (sub-millisecond)
- **Rate Limiting**: 100 requests/minute per IP
- **API Coverage**: 6/6 endpoints tested (100%)
- **Database Indexing**: 5 strategic indexes for query optimization

### **Phase 2: Infrastructure** ✅
- **PostgreSQL**: Connection pooling (20 connections, 10 overflow)
- **9 Specialized Indexes**: GIN, trigram, partial, composite
- **Celery Tasks**: 9 async tasks across 3 queues
- **Structured Logging**: JSON logs with request ID tracking
- **Feature Flags**: 18 flags across 5 categories

### **Phase 3: ML Enhancements** ✅
- **4 ML Models**: Random Forest, XGBoost, LightGBM, Gradient Boosting
- **30+ Features**: Technical, sentiment, temporal, interaction
- **FinBERT**: Financial-specific sentiment (438MB model)
- **SHAP Explainability**: Feature importance for predictions
- **Test Coverage**: 5/5 ML tests passing (100%)

### **Phase 4: Production Integration** ✅
- **Model Monitoring**: Real-time accuracy, drift detection, confidence tracking
- **A/B Testing**: Statistical significance testing for model comparison
- **Feature Store**: Redis caching (100x faster feature access)
- **ML-Enhanced Scoring**: 30% ML weight in signal generation
- **Scheduled Retraining**: Daily automated updates (2 AM UTC)
- **Test Coverage**: 5/5 integration tests passing (100%)

### **Overall System Performance**
- **API Response Time**: <100ms (cached), <500ms (uncached)
- **Feature Access**: <1ms (Redis cache hit)
- **ML Prediction**: <50ms (with feature store)
- **Database Queries**: <10ms (with indexes)
- **RSS Polling**: 20+ feeds in <30 seconds
- **LLM Analysis**: ~5 seconds per article (GPT-4)
- **Model Training**: ~2-5 minutes (depends on data size)

## 📖 Documentation

- **[Architecture](docs/ARCHITECTURE.md)**: System design and data flow
- **[Deployment](docs/DEPLOYMENT.md)**: Production deployment guide
- **[Extending](docs/EXTENDING.md)**: How to add new features
- **[FAQ](http://localhost:5173/faq)**: Frequently asked questions (in-app)
- **[Phase 3 Completion Report](PHASE3_COMPLETION_REPORT.md)**: ML enhancements details
- **[Phase 4 Completion Report](PHASE4_COMPLETION_REPORT.md)**: Production integration details

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

### **Core Technologies**
- **OpenAI** - GPT-4 for LLM analysis
- **yfinance** - Free market data
- **FastAPI** - Modern Python web framework
- **SolidJS** - Reactive UI framework
- **Tailwind CSS** - Utility-first CSS
- **ApexCharts** - Beautiful charts

### **ML & Data Science**
- **scikit-learn** - Machine learning framework
- **XGBoost** - Gradient boosting library
- **LightGBM** - Light gradient boosting
- **HuggingFace Transformers** - FinBERT model
- **PyTorch** - Deep learning backend
- **SHAP** - Model explainability
- **TA-Lib** - Technical analysis indicators

### **Infrastructure**
- **PostgreSQL** - Production database
- **Redis** - Caching and message broker
- **Celery** - Distributed task queue
- **Docker** - Containerization
- **Alembic** - Database migrations
- **SQLAlchemy** - Python ORM

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

