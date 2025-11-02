# Self-Training Research Model System

## Overview

The Research Model is a **self-training online learning system** that continuously improves its predictions by learning from realized market outcomes. It predicts the probability of a positive 3-day return (>1%) based on article analysis features.

### Key Features

- **Online Learning**: Uses River's incremental learning algorithms - no batch retraining required
- **No Look-Ahead Bias**: All features are frozen at article publish time
- **Auto-Labeling**: Automatically generates training labels from realized market returns
- **Thread-Safe**: Concurrent predictions and updates with proper locking
- **Persistent**: Model state saved to disk after each update

## Architecture

```
┌─────────────────┐
│  Article Ingest │
│   (RSS/Manual)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Feature Extract │  ← featurize(analysis)
│  & Validation   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Store Features │  ← ResearchFeatures table
│   (Frozen at    │     (article_id, symbol, published_at, features_json)
│   publish time) │
└─────────────────┘

         ┌──────────────────────────────────┐
         │  Wait N days for market outcome  │
         └──────────────────────────────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │  Auto-Label Job (Daily 2 AM ET)  │
         │  - Compute realized 3-day return │
         │  - Generate binary label (0/1)   │
         │  - Train model incrementally     │
         │  - Store label in DB             │
         └──────────────────────────────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │   Model Continuously Improves    │
         │   (River online learning)        │
         └──────────────────────────────────┘
```

## Components

### 1. Feature Engineering (`app/ml/features.py`)

**Numeric Features:**
- `rsi14` - 14-day RSI
- `atr14` - 14-day ATR
- `gap_pct` - Gap percentage
- `vwap_dev_pct` - VWAP deviation
- `volume_spike_x` - Volume spike multiplier
- `llm_confidence` - LLM confidence score [0-1]
- `trust_score` - Source trust score [0-1]
- `novelty_score` - Novelty score [0-1]
- `sma20_dev_pct` - SMA20 deviation (derived)
- `sma50_dev_pct` - SMA50 deviation (derived)

**Categorical Features:**
- `catalyst_type` - EARNINGS, FDA, M&A, CONTRACT, GUIDANCE, MACRO, OTHER
- `stance` - BULLISH, BEARISH, NEUTRAL
- `sector` - Stock sector

**Key Function:**
```python
from app.ml.features import featurize, validate_features

features = featurize(analysis_payload)
if validate_features(features):
    # Features are ready for model
```

### 2. Online Learning Model (`app/ml/model.py`)

**Pipeline:**
1. `OneHotEncoder` - Handles categorical features
2. `StandardScaler` - Normalizes numeric features
3. `LogisticRegression` - Binary classification with SGD optimizer

**Key Functions:**
```python
from app.ml.model import predict_proba, learn_and_save, get_metrics

# Prediction
prob = predict_proba(features)  # Returns float in [0, 1]

# Training
learn_and_save(features, label)  # label: 0 or 1

# Metrics
metrics = get_metrics()  # {n_samples, log_loss, model_version}
```

**Model Persistence:**
- Saved to: `model_store/research_model.json`
- Auto-saves after each training update
- Loads on startup if exists

### 3. Feature Storage (`app/services/research_store.py`)

Captures frozen feature snapshots at article publish time:

```python
from app.services.research_store import store_features

store_features(
    db=db_session,
    article_id="article_123",
    symbol="AAPL",
    published_at="2025-10-29T14:30:00Z",
    analysis_payload=analysis_dict
)
```

**Database Table: `research_features`**
- `article_id` (PK) - Unique article identifier
- `symbol` - Stock ticker
- `published_at` - ISO8601 timestamp
- `features_json` - JSON snapshot of features
- `created_at` - When features were stored

### 4. Auto-Labeling Job (`app/jobs/research_autolabel.py`)

**Schedule:** Daily at 2 AM ET

**Process:**
1. Find articles published >7 days ago without labels
2. For each article:
   - Determine entry point (next tradeable session after publish)
   - Fetch historical prices
   - Calculate 3-day return from entry
   - Generate label: `1` if return > 1%, else `0`
   - Train model with (features, label)
   - Store label in database

**Entry Point Alignment:**
- After-hours publication → next day open
- Weekend publication → Monday open
- Accounts for market hours and latency

**Database Table: `research_labels`**
- `article_id` (PK) - Links to research_features
- `label` - Binary label (0 or 1)
- `ret_3d` - Actual 3-day return
- `threshold` - Threshold used (0.01 = 1%)
- `entry_day` - ISO8601 date of entry
- `created_at` - When label was generated

### 5. Research API (`app/api/research.py`)

**Endpoints:**

#### POST `/research/predict`
Get model prediction for article analysis.

**Request:**
```json
{
  "analysis": {
    "rsi14": 65.5,
    "atr14": 2.3,
    "sma20": 100.0,
    "sma50": 95.0,
    "adj_close": 102.0,
    "catalyst_type": "EARNINGS",
    "stance": "BULLISH",
    "sector": "TECH",
    "llm_confidence": 0.85,
    "trust_score": 0.9
  }
}
```

**Response:**
```json
{
  "prob_up_3d": 0.73,
  "model_version": "rsm-v1",
  "confidence": "High"
}
```

#### POST `/research/feedback`
Submit human feedback for active learning.

**Request:**
```json
{
  "analysis": { /* same as predict */ },
  "label": 1  // 0 or 1
}
```

**Response:**
```json
{
  "ok": true,
  "message": "Feedback received and model updated"
}
```

#### GET `/research/metrics`
Get current model metrics.

**Response:**
```json
{
  "n_samples": 1523,
  "log_loss": 0.42,
  "model_version": "rsm-v1"
}
```

### 6. Frontend Component (`frontend/src/components/ResearchCard.tsx`)

Displays model predictions in the UI with:
- 3-day probability percentage
- Confidence level (High/Moderate/Neutral/Low/Very Low)
- Color-coded display
- Human feedback buttons (👍 Bullish / 👎 Bearish)
- Disclaimer text

**Usage:**
```tsx
import ResearchCard from './components/ResearchCard';

<ResearchCard 
  analysis={analysisPayload}
  onFeedback={(label) => console.log('User feedback:', label)}
/>
```

## Workflow

### 1. Article Ingestion
When a new article is ingested and analyzed:

```python
# After LLM analysis and technical indicators
from app.services.research_store import store_features

store_features(
    db=db,
    article_id=article.id,
    symbol=article.ticker_guess,
    published_at=article.published_at.isoformat(),
    analysis_payload={
        **technical_indicators,
        **llm_outputs,
        "adj_close": current_price,
        "sector": sector,
    }
)
```

### 2. Auto-Labeling (Scheduled)
Every night at 2 AM ET:

```python
from app.jobs.research_autolabel import run

run(limit=250)  # Process up to 250 unlabeled articles
```

### 3. Real-Time Prediction
When displaying an article:

```python
from app.ml.model import predict_proba
from app.ml.features import featurize

features = featurize(analysis)
prob = predict_proba(features)

# Display to user: "73% probability of +3D return"
```

### 4. Human Feedback (Optional)
User provides feedback via UI:

```python
from app.ml.model import learn_and_save

learn_and_save(features, user_label)
# Model immediately updated
```

## Metrics & Monitoring

**Log Loss:** Lower is better (0 = perfect, 0.693 = random)
- Good: < 0.5
- Acceptable: 0.5 - 0.6
- Needs improvement: > 0.6

**Sample Count:** Number of training examples
- Initial: 0 (untrained)
- After 1 week: ~50-100
- After 1 month: ~500-1000

**Monitor via:**
```bash
curl http://localhost:8000/research/metrics
```

## Configuration

**Return Threshold:**
```python
# backend/app/jobs/research_autolabel.py
RET_THRESHOLD = 0.01  # 1% gain = positive label
```

**Minimum Wait Days:**
```python
# backend/app/jobs/research_autolabel.py
MIN_DAYS_WAIT = 7  # Wait 7 days before labeling
```

**Model Hyperparameters:**
```python
# backend/app/ml/model.py
linear_model.LogisticRegression(
    optimizer=optim.SGD(0.01),  # Learning rate
    l2=1e-4  # L2 regularization
)
```

## Best Practices

1. **Always freeze features at publish time** - Never use future data
2. **Validate features before storage** - Ensure minimum required fields
3. **Monitor log loss** - Track model performance over time
4. **Use human feedback sparingly** - Auto-labeling is primary training source
5. **Review predictions** - Model is for research context, not trading advice

## Troubleshooting

**Model returns 0.5 for all predictions:**
- Model is untrained (n_samples = 0)
- Wait for auto-labeling job to run
- Or provide manual feedback

**Features not being stored:**
- Check `validate_features()` returns True
- Ensure both numeric and categorical features present
- Check database connection

**Auto-labeling not working:**
- Verify scheduler is running
- Check price data availability
- Review logs for errors in `research_autolabel.py`

**High log loss:**
- Model may need more training samples
- Features may not be predictive
- Consider adjusting return threshold

## Future Enhancements

- [ ] Multi-timeframe predictions (1D, 5D, 10D)
- [ ] Sector-specific models
- [ ] Feature importance tracking
- [ ] A/B testing different model architectures
- [ ] Confidence calibration
- [ ] Weekly performance reports

