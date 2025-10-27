# Extending News Tunneler

Guide for adding new features and customizations.

## Adding a New News Source Type

### 1. Update Source Model

Edit `backend/app/models/source.py`:

```python
class SourceType(str, Enum):
    RSS = "rss"
    ATOM = "atom"
    NEWSAPI = "newsapi"
    CUSTOM = "custom"  # Add new type
```

### 2. Implement Parser

Create `backend/app/core/parsers/custom.py`:

```python
async def parse_custom_feed(url: str) -> list[dict]:
    """Parse custom feed format"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10)
        # Parse and return articles
        return [
            {
                "title": "...",
                "summary": "...",
                "url": "...",
                "published_at": datetime.now(),
            }
        ]
```

### 3. Update RSS Module

Edit `backend/app/core/rss.py`:

```python
async def fetch_feed(source: Source) -> list[Article]:
    if source.source_type == SourceType.CUSTOM:
        articles_data = await parse_custom_feed(source.url)
    # ... existing code
```

## Adding a New Scoring Component

### 1. Create Scoring Function

Edit `backend/app/core/scoring.py`:

```python
def score_volume(article: Article) -> float:
    """Score based on trading volume"""
    # Implement volume scoring logic
    return score  # 0-5
```

### 2. Update Score Model

Edit `backend/app/models/score.py`:

```python
class Score(Base):
    # ... existing fields
    volume: float = Column(Float, default=0.0)
```

### 3. Update Settings Model

Edit `backend/app/models/setting.py`:

```python
class Setting(Base):
    # ... existing weights
    weight_volume: float = Column(Float, default=1.0)
```

### 4. Update Scoring Computation

Edit `backend/app/core/scoring.py`:

```python
def compute_total_score(article: Article, settings: Setting) -> float:
    catalyst = score_catalyst(article)
    novelty = score_novelty(article)
    credibility = score_credibility(article)
    sentiment = score_sentiment(article)
    liquidity = score_liquidity(article)
    volume = score_volume(article)  # Add new component
    
    total = (
        catalyst * settings.weight_catalyst +
        novelty * settings.weight_novelty +
        credibility * settings.weight_credibility +
        sentiment * settings.weight_sentiment +
        liquidity * settings.weight_liquidity +
        volume * settings.weight_volume  # Add new weight
    )
    return total
```

### 5. Update Frontend

Edit `frontend/src/components/WeightSliders.tsx`:

```typescript
const weights = [
    // ... existing weights
    { key: 'weight_volume', label: 'Volume Weight', description: 'Impact of trading volume' },
]
```

## Adding a New Notification Channel

### 1. Create Notifier

Create `backend/app/core/notifiers/telegram.py`:

```python
async def send_telegram_notification(article: Article, chat_id: str):
    """Send alert via Telegram"""
    message = f"🚨 {article.title}\nScore: {article.score.total}"
    # Send via Telegram API
```

### 2. Update Notifiers Module

Edit `backend/app/core/notifiers.py`:

```python
async def notify_article(article: Article, settings: Setting):
    # ... existing notifications
    if settings.telegram_enabled:
        await send_telegram_notification(article, settings.telegram_chat_id)
```

### 3. Update Settings

Edit `backend/app/models/setting.py`:

```python
class Setting(Base):
    # ... existing fields
    telegram_chat_id: str = Column(String, nullable=True)
```

## Adding a New API Endpoint

### 1. Create Route

Create `backend/app/api/custom.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db

router = APIRouter(prefix="/api/custom", tags=["custom"])

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get custom statistics"""
    # Implement endpoint
    return {"data": "..."}
```

### 2. Register Route

Edit `backend/app/main.py`:

```python
from app.api import custom

app.include_router(custom.router)
```

## Adding a New Frontend Page

### 1. Create Page Component

Create `frontend/src/pages/Custom.tsx`:

```typescript
export default function Custom() {
  return (
    <div>
      <h1 class="text-3xl font-bold mb-8">Custom Page</h1>
      {/* Page content */}
    </div>
  )
}
```

### 2. Add Route

Edit `frontend/src/App.tsx`:

```typescript
<Route path="/custom" component={Custom} />
```

### 3. Add Navigation Link

Edit `frontend/src/components/Navigation.tsx`:

```typescript
<A href="/custom" class="...">
  Custom
</A>
```

## Adding Database Migrations

### 1. Create Migration

```bash
cd backend
alembic revision --autogenerate -m "Add new column"
```

### 2. Edit Migration File

Edit `backend/alembic/versions/XXX_add_new_column.py`:

```python
def upgrade() -> None:
    op.add_column('article', sa.Column('new_field', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('article', 'new_field')
```

### 3. Apply Migration

```bash
alembic upgrade head
```

## Adding Tests

### Backend Tests

Create `backend/tests/test_custom.py`:

```python
import pytest
from app.core.custom import custom_function

def test_custom_function():
    result = custom_function()
    assert result == expected_value
```

Run tests:

```bash
pytest tests/test_custom.py -v
```

## Environment Variables

Add new env vars to `.env.example`:

```env
# Custom Feature
CUSTOM_API_KEY=your-key-here
CUSTOM_ENABLED=true
```

Load in `backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings
    custom_api_key: str = Field(default="", env="CUSTOM_API_KEY")
    custom_enabled: bool = Field(default=False, env="CUSTOM_ENABLED")
```

## Performance Optimization

### Database Queries
- Use indexes for frequently queried columns
- Use `select()` with specific columns instead of `*`
- Batch operations when possible

### Caching
- Cache settings in memory (singleton pattern)
- Use Redis for distributed caching (future)

### Async Operations
- Use `asyncio` for concurrent operations
- Use `httpx.AsyncClient` for HTTP requests
- Use `asyncio.gather()` for parallel tasks

## Code Style

### Backend
- Follow PEP 8
- Use type hints
- Use docstrings for functions
- Use context managers for resource cleanup

### Frontend
- Use TypeScript for type safety
- Use Solid.js reactive patterns
- Use Tailwind CSS for styling
- Use component composition

## Debugging

### Backend
```bash
# Enable debug logging
LOG_LEVEL=debug python -m uvicorn app.main:app --reload

# Use debugger
import pdb; pdb.set_trace()
```

### Frontend
```bash
# Browser DevTools
F12 or Cmd+Option+I

# Console logging
console.log("Debug:", value)
```

## Common Tasks

### Add a new keyword for catalyst scoring
Edit `backend/app/core/scoring.py`:

```python
CATALYST_KEYWORDS = {
    "merger": 5,
    "acquisition": 5,
    "bankruptcy": 4,
    "new_keyword": 3,  # Add here
}
```

### Change default alert threshold
Edit `backend/app/models/setting.py`:

```python
min_alert_score: float = Column(Float, default=15.0)  # Changed from 12.0
```

### Add new ticker symbols
Edit `backend/app/seeds/tickers.json`:

```json
[
  "AAPL",
  "GOOGL",
  "NEW_TICKER"
]
```

## Troubleshooting

### Changes not reflected
- Restart development server
- Clear browser cache (Ctrl+Shift+Delete)
- Check for TypeScript errors

### Database issues
- Check migrations: `alembic current`
- Reset database: `rm backend/app.db`
- Re-seed: `make seed`

### WebSocket issues
- Check browser console for errors
- Verify backend is running
- Check VITE_WS_URL in frontend/.env.local

