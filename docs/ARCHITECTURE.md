# News Tunneler Architecture

## System Overview

News Tunneler is a distributed system for real-time news scoring and alerting:

```
RSS/Atom/NewsAPI Feeds
        ↓
    [Backend]
        ├─ Fetch & Parse (feedparser)
        ├─ Deduplicate (URL + title hash)
        ├─ Score (5-factor algorithm)
        ├─ Persist (SQLite)
        └─ Broadcast (WebSocket + Notifications)
        ↓
    [Frontend]
        ├─ Real-time Dashboard
        ├─ Alert Management
        ├─ Source Configuration
        └─ Scoring Controls
```

## Backend Architecture

### Core Modules

#### `core/config.py`
- Pydantic Settings for environment configuration
- Properties for checking optional services (Slack, Email, NewsAPI)
- Singleton pattern for app-wide settings

#### `core/db.py`
- SQLAlchemy engine and session management
- Context managers for proper resource cleanup
- Dependency injection for FastAPI routes

#### `core/scoring.py`
- `score_catalyst()`: Regex-based keyword matching
- `score_novelty()`: Time-based scoring
- `score_credibility()`: Domain-based scoring
- `compute_total_score()`: Weighted sum calculation

#### `core/sentiment.py`
- VADER sentiment analysis
- Compound score mapping to 1-4 scale

#### `core/tickers.py`
- Ticker symbol extraction from text
- Regex-based pattern matching

#### `core/dedupe.py`
- URL-based deduplication (primary)
- Title hash fallback
- `article_exists()` function

#### `core/rss.py`
- feedparser integration
- Async HTTP fetching with httpx
- Error handling and retries

#### `core/notifiers.py`
- Slack webhook notifications
- Email notifications (SMTP)
- Debouncing (1-hour window)
- Async notification dispatch

#### `core/scheduler.py`
- APScheduler integration
- `poll_feeds()`: Main polling function
- Fetches → Dedupes → Scores → Broadcasts
- Configurable interval (default: 15 minutes)

### Data Models

#### Source
```python
- id: int (PK)
- url: str (unique)
- name: str
- source_type: enum (RSS, ATOM, NEWSAPI)
- enabled: bool
- created_at: datetime
- last_fetched_at: datetime (nullable)
```

#### Article
```python
- id: int (PK)
- url: str (unique, indexed)
- title: str
- summary: str (nullable)
- source_id: int (FK)
- source_name: str
- source_url: str
- source_type: str
- published_at: datetime (indexed)
- ticker_guess: str (nullable, indexed)
- created_at: datetime
```

#### Score
```python
- id: int (PK)
- article_id: int (FK, unique)
- catalyst: float (0-5)
- novelty: float (0-5)
- credibility: float (0-5)
- sentiment: float (1-4)
- liquidity: float (0-5)
- total: float (computed)
- created_at: datetime
```

#### Setting
```python
- id: int (PK, always 1)
- weight_catalyst: float (default: 1.0)
- weight_novelty: float (default: 1.0)
- weight_credibility: float (default: 1.0)
- weight_sentiment: float (default: 1.0)
- weight_liquidity: float (default: 1.0)
- min_alert_score: float (default: 12.0)
- poll_interval_sec: int (default: 900)
- updated_at: datetime
```

#### Webhook
```python
- id: int (PK)
- article_id: int (FK)
- notification_type: enum (SLACK, EMAIL)
- status: enum (PENDING, SENT, FAILED)
- error_message: str (nullable)
- created_at: datetime
- sent_at: datetime (nullable)
```

### API Routes

#### Articles (`/api/articles`)
- `GET /api/articles`: List with filtering
  - Query params: `q`, `min_score`, `ticker`, `domain`, `since`, `limit`, `offset`
  - Returns: `ArticleResponse[]` with optional score
- `GET /api/articles/{id}`: Get single article

#### Sources (`/api/sources`)
- `GET /api/sources`: List all sources
- `POST /api/sources`: Create source (validates URL reachability)
- `PATCH /api/sources/{id}`: Enable/disable
- `DELETE /api/sources/{id}`: Delete source

#### Settings (`/api/settings`)
- `GET /api/settings`: Get current settings
- `PATCH /api/settings`: Update weights and thresholds

#### WebSocket (`/ws/alerts`)
- Maintains list of active connections
- Broadcasts alerts to all connected clients
- Message format: `{"type": "alert", "data": Article}`

### Background Jobs

#### Poll Feeds (APScheduler)
Runs every `poll_interval_sec` (default: 900s = 15 min):

1. Fetch all enabled sources
2. Parse feeds (RSS/Atom/NewsAPI)
3. Deduplicate articles
4. Score articles
5. Persist to database
6. Broadcast to WebSocket clients
7. Send notifications (if enabled)

## Frontend Architecture

### State Management (Zustand)

```typescript
interface Store {
  // Articles
  articles: Article[]
  setArticles()
  addArticle()

  // Live alerts
  liveAlerts: Article[]
  addLiveAlert()
  clearLiveAlerts()

  // Settings
  settings: Settings | null
  setSettings()

  // Filters
  filters: Filters
  setFilters()

  // UI
  darkMode: boolean
  toggleDarkMode()
  isConnected: boolean
  setIsConnected()
}
```

### API Client (`lib/api.ts`)

- Axios instance with base URL
- Functions for all REST endpoints
- Error handling and type safety

### WebSocket Client (`lib/ws.ts`)

- Auto-reconnect with exponential backoff
- Max 5 reconnection attempts
- 3-second delay between attempts
- Broadcasts alerts to store

### Components

#### Navigation
- Logo and page links
- Connection status indicator
- Dark mode toggle

#### Kpis
- 24h alert count
- Average score
- Top 5 tickers

#### AlertRow
- Article title (clickable link)
- Summary preview
- Source badge
- Ticker badge
- Score with color coding
- Published time (relative)

#### AlertTable
- Paginated article list (20 per page)
- Sortable columns
- Responsive design

#### SourceForm
- URL and name inputs
- Feed type selector (RSS/Atom/NewsAPI)
- Validation and error handling

#### WeightSliders
- 5 sliders for scoring weights
- Range: 0-5 with 0.1 step
- Real-time value display

### Pages

#### Dashboard
- KPI cards
- Live alerts table (top 10)
- Real-time updates

#### Alerts
- Advanced filtering (search, score, ticker)
- Paginated results
- Filter controls

#### Sources
- Add new source form
- Source list with status
- Enable/disable toggle
- Delete button

#### Settings
- Weight sliders
- Alert threshold slider
- Poll interval input
- Scoring formula info

## Data Flow

### Ingestion Pipeline

```
1. Scheduler triggers poll_feeds()
2. Fetch enabled sources
3. Parse feeds (feedparser)
4. Extract articles
5. Deduplicate (URL + title hash)
6. Extract tickers
7. Analyze sentiment
8. Score articles (5-factor)
9. Persist to database
10. Broadcast to WebSocket
11. Send notifications (debounced)
```

### Real-time Alert Flow

```
Backend                          Frontend
   ↓
poll_feeds()
   ↓
score_article()
   ↓
broadcast_alert()
   ├─ WebSocket message
   └─ Notification (Slack/Email)
                                    ↓
                            WebSocket receives
                                    ↓
                            store.addLiveAlert()
                                    ↓
                            Dashboard updates
```

## Error Handling

### Network Errors
- Retry logic with exponential backoff (tenacity)
- Max 3 retries for feed fetching
- Graceful degradation

### Database Errors
- Context managers for session cleanup
- Transaction rollback on error
- Unique constraint handling for deduplication

### WebSocket Errors
- Auto-reconnect on disconnect
- Max 5 reconnection attempts
- Fallback to REST API

## Performance Considerations

### Database
- Indexes on `published_at`, `ticker_guess`, `url`
- Unique constraint on `article.url`
- Unique constraint on `score.article_id`

### Caching
- Settings cached in memory (singleton)
- Lazy loading of articles

### Async Operations
- Async HTTP requests (httpx)
- Async database operations (SQLAlchemy async)
- Non-blocking WebSocket broadcasts

## Security

### Authentication
- Optional admin token in `.env`
- Token validation on protected endpoints (ready to implement)

### Input Validation
- Pydantic models for all inputs
- URL validation for sources
- SQL injection prevention (SQLAlchemy ORM)

### CORS
- Configured for localhost development
- Configurable for production

## Deployment

### Docker
- Multi-stage builds for optimization
- Health checks for both services
- Volume mounts for database persistence

### Environment
- Separate configs for dev/prod
- Environment variables for secrets
- `.env.example` for reference

## Monitoring & Logging

### Logging
- Structured logging with Python logging
- Log level configurable via `LOG_LEVEL` env var

### Health Checks
- `/health` endpoint for backend
- Docker health checks
- WebSocket connection status in UI

## Future Enhancements

1. **Authentication**: Implement admin token validation
2. **CSV Export**: Export alerts to CSV
3. **SEC Links**: Quick link to SEC.gov for detected companies
4. **Score Tooltips**: Show component breakdown on hover
5. **Advanced Filtering**: Save and load filter presets
6. **Notifications**: SMS, Telegram, Discord
7. **Analytics**: Dashboard with historical trends
8. **Machine Learning**: Improve scoring with ML models

