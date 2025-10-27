# News Tunneler - Complete File Index

## Root Directory

```
news-tunneler/
├── README.md                    # Main project documentation
├── QUICKSTART.md               # 5-minute setup guide
├── PROJECT_COMPLETION.md       # Project status and summary
├── FILE_INDEX.md               # This file
├── Makefile                    # Root make commands
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── docker-compose.yml          # Docker Compose configuration
└── docs/                       # Documentation directory
```

## Backend Directory (`backend/`)

### Configuration & Setup
- `requirements.txt` - Python dependencies
- `Dockerfile` - Backend Docker image
- `Makefile` - Backend make commands
- `README.md` - Backend documentation
- `alembic.ini` - Database migration config

### Application Code (`app/`)

#### Core Modules (`app/core/`)
- `__init__.py` - Package initialization
- `config.py` - Pydantic Settings configuration
- `db.py` - SQLAlchemy engine and session management
- `logging.py` - Logging configuration
- `scoring.py` - 5-factor scoring algorithm
- `sentiment.py` - VADER sentiment analysis
- `tickers.py` - Ticker symbol extraction
- `dedupe.py` - Article deduplication logic
- `rss.py` - RSS/Atom/NewsAPI feed parsing
- `notifiers.py` - Slack/Email notifications
- `scheduler.py` - APScheduler background jobs

#### Models (`app/models/`)
- `__init__.py` - Package initialization
- `base.py` - SQLAlchemy Base class
- `source.py` - Source model (RSS/Atom/NewsAPI feeds)
- `article.py` - Article model
- `score.py` - Score model (scoring breakdown)
- `setting.py` - Setting model (weights and thresholds)
- `webhook.py` - Webhook model (notification history)

#### API Routes (`app/api/`)
- `__init__.py` - Package initialization
- `articles.py` - Article endpoints (GET, filtering)
- `sources.py` - Source endpoints (CRUD)
- `settings.py` - Settings endpoints (GET, PATCH)
- `websocket.py` - WebSocket endpoint for alerts

#### Seeds (`app/seeds/`)
- `seed.py` - Seed script for database population
- `seed_sources.json` - 10 sample RSS feeds
- `seed_articles.json` - 20 sample articles

#### Data (`app/data/`)
- `tickers.json` - 100 ticker symbols

#### Main Application
- `__init__.py` - Package initialization
- `main.py` - FastAPI application entry point

### Database Migrations (`alembic/`)
- `env.py` - Alembic environment configuration
- `script.py.mako` - Migration template
- `versions/001_initial_schema.py` - Initial database schema

### Tests (`tests/`)
- `test_scoring.py` - Scoring algorithm tests
- `test_dedupe.py` - Deduplication tests
- `test_api_articles.py` - API endpoint tests

## Frontend Directory (`frontend/`)

### Configuration & Setup
- `package.json` - Node.js dependencies
- `tsconfig.json` - TypeScript configuration
- `tsconfig.node.json` - TypeScript config for build tools
- `vite.config.ts` - Vite build configuration
- `tailwind.config.js` - Tailwind CSS configuration
- `postcss.config.js` - PostCSS configuration
- `index.html` - HTML entry point
- `Dockerfile` - Frontend Docker image
- `Makefile` - Frontend make commands
- `README.md` - Frontend documentation
- `.env.example` - Environment template

### Source Code (`src/`)

#### Main Application
- `main.tsx` - Application entry point
- `App.tsx` - Root component with routing
- `app.css` - Global styles with Tailwind directives

#### Components (`src/components/`)
- `Navigation.tsx` - Navigation bar with links and status
- `Kpis.tsx` - KPI cards (24h alerts, avg score, top tickers)
- `AlertRow.tsx` - Single alert row in table
- `AlertTable.tsx` - Paginated alerts table
- `SourceForm.tsx` - Form to add new news sources
- `WeightSliders.tsx` - Sliders for scoring weights

#### Pages (`src/pages/`)
- `Dashboard.tsx` - Main dashboard with KPIs and live alerts
- `Alerts.tsx` - Alerts page with advanced filtering
- `Sources.tsx` - Source management page
- `Settings.tsx` - Settings page for weights and thresholds

#### Libraries (`src/lib/`)
- `api.ts` - Axios API client with all endpoints
- `ws.ts` - WebSocket client with auto-reconnect
- `store.ts` - Zustand state management store

## Documentation (`docs/`)

- `ARCHITECTURE.md` - System architecture and design
- `EXTENDING.md` - Guide for adding new features
- `DEPLOYMENT.md` - Production deployment guide

## File Statistics

### Backend
- Python files: 30+
- Test files: 3
- Configuration files: 5
- Total: 38+ files

### Frontend
- TypeScript/TSX files: 15
- Configuration files: 7
- Total: 22+ files

### Documentation
- Markdown files: 8
- Total: 8 files

### Infrastructure
- Docker files: 2
- Compose file: 1
- Makefile: 3
- Total: 6 files

**Grand Total: 74+ files**

## Key File Relationships

### Backend Flow
```
main.py
├── config.py (settings)
├── db.py (database)
├── scheduler.py (background jobs)
│   ├── rss.py (feed fetching)
│   ├── dedupe.py (deduplication)
│   ├── scoring.py (scoring)
│   └── notifiers.py (notifications)
├── api/
│   ├── articles.py
│   ├── sources.py
│   ├── settings.py
│   └── websocket.py
└── models/
    ├── source.py
    ├── article.py
    ├── score.py
    ├── setting.py
    └── webhook.py
```

### Frontend Flow
```
main.tsx
├── App.tsx (routing)
│   ├── Navigation.tsx
│   ├── Dashboard.tsx
│   │   ├── Kpis.tsx
│   │   └── AlertRow.tsx
│   ├── Alerts.tsx
│   │   └── AlertTable.tsx
│   ├── Sources.tsx
│   │   └── SourceForm.tsx
│   └── Settings.tsx
│       └── WeightSliders.tsx
└── lib/
    ├── api.ts (HTTP client)
    ├── ws.ts (WebSocket client)
    └── store.ts (state management)
```

## Configuration Files

### Environment
- `.env.example` - Template for environment variables
- `backend/.env.example` - Backend-specific template
- `frontend/.env.example` - Frontend-specific template

### Build & Deployment
- `docker-compose.yml` - Multi-container orchestration
- `backend/Dockerfile` - Backend image
- `frontend/Dockerfile` - Frontend image
- `backend/Makefile` - Backend commands
- `frontend/Makefile` - Frontend commands
- `Makefile` - Root commands

### Database
- `alembic.ini` - Migration configuration
- `backend/alembic/env.py` - Migration environment

### Build Tools
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - Node.js dependencies
- `frontend/tsconfig.json` - TypeScript config
- `frontend/vite.config.ts` - Vite config
- `frontend/tailwind.config.js` - Tailwind config
- `frontend/postcss.config.js` - PostCSS config

## Data Files

### Seeds
- `backend/app/seeds/seed_sources.json` - 10 RSS feeds
- `backend/app/seeds/seed_articles.json` - 20 articles
- `backend/app/seeds/seed.py` - Seed script

### Reference Data
- `backend/app/data/tickers.json` - 100 ticker symbols

## Testing Files

- `backend/tests/test_scoring.py` - Scoring tests
- `backend/tests/test_dedupe.py` - Deduplication tests
- `backend/tests/test_api_articles.py` - API tests

## Documentation Files

- `README.md` - Main documentation
- `QUICKSTART.md` - Quick start guide
- `PROJECT_COMPLETION.md` - Project status
- `FILE_INDEX.md` - This file
- `docs/ARCHITECTURE.md` - Architecture documentation
- `docs/EXTENDING.md` - Extension guide
- `docs/DEPLOYMENT.md` - Deployment guide
- `backend/README.md` - Backend documentation
- `frontend/README.md` - Frontend documentation

## Version Control

- `.gitignore` - Git ignore rules

## Total Project Size

- **Backend**: ~2,000 lines of Python code
- **Frontend**: ~1,500 lines of TypeScript/TSX code
- **Tests**: ~300 lines of test code
- **Documentation**: ~2,000 lines of markdown
- **Configuration**: ~500 lines of config files

**Total: ~6,300 lines of code and documentation**

## Quick Navigation

### To understand the project
1. Start with `README.md`
2. Read `QUICKSTART.md` for setup
3. Review `docs/ARCHITECTURE.md` for design

### To run the project
1. Follow `QUICKSTART.md`
2. Use commands from root `Makefile`

### To extend the project
1. Read `docs/EXTENDING.md`
2. Review relevant source files
3. Add tests in `backend/tests/`

### To deploy
1. Read `docs/DEPLOYMENT.md`
2. Configure `.env` file
3. Use Docker or manual deployment

---

**Last Updated**: 2025-10-27
**Status**: Complete and Production-Ready

