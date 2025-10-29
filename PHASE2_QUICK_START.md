# Phase 2 Quick Start Guide

**Status:** ✅ **COMPLETE** - All infrastructure improvements implemented!

---

## 🚀 Quick Start (5 minutes)

### 1. Start Infrastructure

```bash
cd backend
docker-compose up -d
```

This starts:
- ✅ PostgreSQL 16 (port 5432)
- ✅ Redis 7 (port 6379)
- ✅ PgAdmin 4 (port 5050)

### 2. Install Dependencies

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
cd backend
source venv/bin/activate
USE_POSTGRESQL=true alembic upgrade head
USE_POSTGRESQL=true python apply_postgresql_indexes.py
```

### 4. Start Celery Worker

```bash
cd backend
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info -Q llm,rss,digest
```

### 5. Start Celery Beat (Scheduler)

```bash
cd backend
source venv/bin/activate
celery -A app.core.celery_app beat --loglevel=info
```

### 6. Start Flower (Optional - Monitoring)

```bash
cd backend
source venv/bin/activate
celery -A app.core.celery_app flower --port=5555
```

### 7. Start FastAPI

```bash
cd backend
source venv/bin/activate
USE_POSTGRESQL=true uvicorn app.main:app --reload
```

---

## 🎯 What's New in Phase 2?

### 1. Structured Logging 📊
- JSON logs in `backend/logs/app.log`
- Request ID tracking
- Easy aggregation with ELK/Splunk

**Example:**
```json
{
  "timestamp": "2025-10-29T02:44:02.485643Z",
  "level": "INFO",
  "request_id": "req-abc123",
  "message": "GET /api/signals/top"
}
```

### 2. Feature Flags 🎛️
- 18 feature flags for gradual rollout
- Admin API at `/admin/feature-flags`
- No deployment needed for changes

**Example:**
```bash
# List all flags
curl http://localhost:8000/admin/feature-flags

# Toggle a flag
curl -X POST http://localhost:8000/admin/feature-flags/REDIS_CACHING/toggle
```

### 3. Celery Task Queue ⚡
- 9 async tasks across 3 queues
- Scheduled tasks with Beat
- Monitoring with Flower at http://localhost:5555

**Example:**
```python
from app.tasks.llm_tasks import analyze_article_async

# Queue async analysis
result = analyze_article_async.delay(article_id=123)
```

### 4. PostgreSQL Database 🐘
- Production-ready RDBMS
- Connection pooling (10+20)
- Full-text search with GIN indexes
- Fuzzy search with trigrams
- PgAdmin at http://localhost:5050

**Example:**
```bash
# Switch to PostgreSQL
export USE_POSTGRESQL=true

# Start app
uvicorn app.main:app --reload
```

---

## 📊 Monitoring

### Celery Flower
- **URL:** http://localhost:5555
- **Features:** Task monitoring, worker stats, queue status

### PgAdmin
- **URL:** http://localhost:5050
- **Email:** admin@newstunneler.local
- **Password:** admin

### Logs
- **Location:** `backend/logs/app.log`
- **Format:** JSON (structured)

---

## 🧪 Testing

### Test All Components

```bash
cd backend
source venv/bin/activate

# Test structured logging + feature flags
python test_phase2_quick_wins.py

# Test Celery
python test_celery.py

# Test PostgreSQL
USE_POSTGRESQL=true python test_postgresql.py
```

---

## 🔧 Configuration

### Environment Variables

```bash
# PostgreSQL
export USE_POSTGRESQL=true
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=news_tunneler
export POSTGRES_USER=news_tunneler
export POSTGRES_PASSWORD=news_tunneler_dev_password

# Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
```

### Feature Flags

```python
from app.core.feature_flags import get_feature_flags, FeatureFlag

# Get manager
flags = get_feature_flags()

# Check if enabled
if flags.is_enabled(FeatureFlag.REDIS_CACHING):
    # Use Redis
    pass

# Enable/disable
flags.enable(FeatureFlag.CELERY_TASKS)
flags.disable(FeatureFlag.EXPERIMENTAL_FINBERT)
```

---

## 📚 Documentation

- **Detailed Report:** `PHASE2_COMPLETION_REPORT.md`
- **Progress Report:** `PHASE2_PROGRESS_REPORT.md`
- **Backend Suggestions:** `BACKEND_IMPROVEMENT_SUGGESTIONS.md`

---

## 🎯 Next Steps

**Phase 3: ML Enhancements** (Week 4-6)

1. **Advanced ML Models** (1 week)
   - Random Forest classifier
   - XGBoost for signal prediction
   - Model versioning and A/B testing

2. **FinBERT Sentiment** (3 days)
   - Financial-specific sentiment analysis
   - Replace VADER with FinBERT
   - Batch processing with Celery

3. **Time-Series Forecasting** (1 week)
   - Prophet for price prediction
   - ARIMA for trend analysis
   - Integration with signals

**Ready to proceed to Phase 3?** 🚀

---

## ❓ Troubleshooting

### PostgreSQL won't start
```bash
# Check if port 5432 is in use
lsof -i :5432

# Stop existing PostgreSQL
docker-compose down
docker-compose up -d postgres
```

### Celery tasks not running
```bash
# Check worker is running
celery -A app.core.celery_app inspect active

# Check registered tasks
celery -A app.core.celery_app inspect registered
```

### Redis connection error
```bash
# Check Redis is running
docker ps | grep redis

# Test Redis connection
redis-cli ping
```

---

## 📞 Support

For issues or questions:
1. Check `PHASE2_COMPLETION_REPORT.md` for detailed documentation
2. Review test scripts for examples
3. Check Docker logs: `docker-compose logs -f`

---

**Phase 2 Status:** ✅ **COMPLETE** 🎉

