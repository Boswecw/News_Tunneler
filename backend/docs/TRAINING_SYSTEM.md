# Price Prediction Training System

## Overview

The News Tunneler application now features a **dual-model ML architecture**:

1. **Research Model** (`/api/research/*`) - Online learning model using River for article-based predictions
2. **Price Prediction Model** (`/api/training/*`) - Batch-trained scikit-learn models for price forecasting

This document describes the Price Prediction Training System, which complements the existing research model by providing historical price-based forecasting capabilities.

## Architecture

### Dual-Model System

```
┌─────────────────────────────────────────────────────────────┐
│                    News Tunneler ML System                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐      ┌──────────────────────┐    │
│  │   Research Model     │      │  Price Prediction    │    │
│  │   (Online Learning)  │      │  (Batch Training)    │    │
│  ├──────────────────────┤      ├──────────────────────┤    │
│  │ • River framework    │      │ • scikit-learn       │    │
│  │ • Article features   │      │ • OHLCV data         │    │
│  │ • Incremental        │      │ • Technical          │    │
│  │ • Auto-labeling      │      │   indicators         │    │
│  │ • 3-day returns      │      │ • Next-day forecast  │    │
│  └──────────────────────┘      └──────────────────────┘    │
│           ↓                              ↓                   │
│  /api/research/predict          /api/training/predict       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Differences

| Feature | Research Model | Price Prediction Model |
|---------|---------------|------------------------|
| **Learning Type** | Online (incremental) | Batch (periodic retraining) |
| **Data Source** | Article analysis + market data | Historical OHLCV only |
| **Features** | LLM outputs, sentiment, technical indicators | Technical indicators only |
| **Target** | 3-day return probability | Next-day close price |
| **Training Trigger** | Auto-labeling job (daily 2 AM) | Manual API call |
| **Model Type** | LogisticRegression (River) | Ridge/RandomForest (sklearn) |
| **Use Case** | Article impact prediction | Price trend forecasting |

## Components

### 1. Model Registry (`app/services/model_registry.py`)

Manages metadata for all trained price prediction models.

**Key Features:**
- Parameter hashing for reproducibility
- Version tracking (Python, sklearn, pandas, numpy, yfinance)
- Training metrics (R², RMSE, MAE)
- Date range tracking
- Archive path management

**Registry Structure:**
```json
{
  "AAPL_10y": {
    "ticker": "AAPL",
    "mode": "10y",
    "param_hash": "a1b2c3d4e5f6g7h8",
    "r2_score": 0.85,
    "n_observations": 2500,
    "trained_at": "2025-10-29T12:00:00Z",
    "model_path": "backend/models/AAPL_10y.pkl",
    "python_version": "3.12.0",
    "sklearn_version": "1.3.2",
    "pandas_version": "2.2.0",
    "numpy_version": "1.26.2",
    "yfinance_version": "0.2.66",
    "date_range_start": "2015-10-29",
    "date_range_end": "2025-10-29",
    "indicator_config": {...},
    "archive_path": "backend/models/archives/AAPL_10y_2025-10-29.parquet.gz"
  }
}
```

### 2. Price Model Training (`app/ml/price_model.py`)

Core training logic with technical indicator engineering.

**Technical Indicators:**
- **Moving Averages:** SMA (5, 10, 20, 50), EMA (12, 26)
- **Momentum:** RSI (14-period)
- **Trend:** MACD (12/26/9)
- **Volatility:** Bollinger Bands (20-period, 2σ), ATR (14-period)
- **Volume:** Volume ratio vs 20-day SMA
- **Returns:** 1-day, 5-day, 20-day percentage changes

**Training Modes:**

#### 5-Year Mode (`mode="5y"`)
- **Data:** 5 years of daily OHLCV
- **Model:** Ridge Regression (L2 regularization)
- **Weighting:** Uniform (all samples weighted equally)
- **Use Case:** Fast baseline, quick retraining
- **Training Time:** ~10-30 seconds

#### 10-Year Mode (`mode="10y"`)
- **Data:** 10 years of daily OHLCV
- **Model:** Random Forest (100 trees, max_depth=10)
- **Weighting:** Exponential time-decay (half-life = 365 days)
- **Use Case:** Robust production model
- **Training Time:** ~1-3 minutes

**Time-Decay Weighting:**
```python
weight = 0.5^(days_ago / half_life)
```
More recent data receives higher weight, allowing the model to adapt to changing market conditions while still learning from historical patterns.

### 3. Training API (`app/api/training.py`)

FastAPI router providing training and prediction endpoints.

**Endpoints:**

#### `POST /api/training/train/{ticker}`
Train a price prediction model.

**Query Parameters:**
- `mode`: `"5y"` or `"10y"` (default: `"10y"`)
- `retain`: `"none"`, `"window"`, or `"all"` (default: `"none"`)
- `window_days`: Days to retain if `retain="window"` (default: 180)
- `archive`: Archive training data to Parquet (default: `false`)

**Response:**
```json
{
  "ticker": "AAPL",
  "mode": "10y",
  "model_path": "backend/models/AAPL_10y.pkl",
  "r2_score": 0.85,
  "n_observations": 2500,
  "trained_at": "2025-10-29T12:00:00Z",
  "param_hash": "a1b2c3d4e5f6g7h8",
  "archive_path": "backend/models/archives/AAPL_10y_2025-10-29.parquet.gz",
  "pruned_rows": 2500
}
```

#### `GET /api/training/predict/{ticker}`
Get next-day price prediction.

**Query Parameters:**
- `mode`: `"5y"` or `"10y"` (default: `"10y"`)

**Response:**
```json
{
  "ticker": "AAPL",
  "mode": "10y",
  "predicted_close": 175.50,
  "current_close": 173.25,
  "predicted_change_pct": 1.30,
  "model_trained_at": "2025-10-29T12:00:00Z",
  "features_snapshot": {
    "sma_5": 172.80,
    "sma_20": 170.50,
    "rsi": 65.3,
    "macd": 1.25,
    ...
  }
}
```

#### `POST /api/training/prune`
Bulk prune historical data.

**Query Parameters:**
- `retain`: `"none"` or `"window"` (default: `"window"`)
- `window_days`: Days to retain if `retain="window"` (default: 180)

**Response:**
```json
{
  "pruned_rows": 5000,
  "retained_rows": 180,
  "vacuum_completed": true
}
```

#### `GET /api/training/models`
List all trained models.

**Response:**
```json
{
  "models": [
    {
      "ticker": "AAPL",
      "mode": "10y",
      "r2_score": 0.85,
      "n_observations": 2500,
      "trained_at": "2025-10-29T12:00:00Z",
      ...
    }
  ],
  "total_count": 1
}
```

## Data Management

### Ephemeral Training Dataset Policy

Historical price data is **ephemeral** - used only during training, then pruned according to retention policy.

**Retention Policies:**

1. **`retain="none"`** (Production Default)
   - Deletes ALL historical data after training
   - Keeps only trained model artifacts
   - Minimizes storage footprint
   - Recommended for production deployments

2. **`retain="window"`**
   - Keeps most recent N days (default: 180)
   - Useful for incremental retraining
   - Balances storage vs. flexibility
   - Recommended for development

3. **`retain="all"`**
   - Keeps all downloaded data
   - For debugging and analysis only
   - NOT recommended for production

### Storage Optimization

**After Training:**
1. Apply retention policy (delete old data)
2. Run `VACUUM` to reclaim SQLite space
3. Compress model with `joblib` (compress=3)
4. Optionally archive to Parquet with gzip

**Storage Breakdown:**
- **Model file:** ~1-5 MB (compressed)
- **Registry:** ~1-10 KB
- **Archive (optional):** ~500 KB - 2 MB (Parquet + gzip)
- **Database (retain=none):** 0 bytes
- **Database (retain=window, 180 days):** ~50-100 KB per ticker

## Workflow

### Training Workflow

```
1. Download historical data (yfinance)
   ↓
2. Store in SQLite (historical_prices table)
   ↓
3. Calculate technical indicators
   ↓
4. Prepare features and target
   ↓
5. Apply time-decay weights (10y mode only)
   ↓
6. Train model (Ridge or RandomForest)
   ↓
7. Evaluate model (R², RMSE, MAE)
   ↓
8. Save model to disk (compressed)
   ↓
9. Update registry with metadata
   ↓
10. Archive data (if requested)
   ↓
11. Prune historical data (per retention policy)
   ↓
12. VACUUM database
```

### Prediction Workflow

```
1. Load model from registry
   ↓
2. Download recent data (3 months)
   ↓
3. Calculate indicators
   ↓
4. Extract latest features
   ↓
5. Make prediction
   ↓
6. Return forecast + feature snapshot
```

## Testing

### Unit Tests (`tests/test_training_unit.py`)

**Coverage:**
- Indicator calculation correctness
- Time-decay weight monotonicity
- Walk-forward split validation
- Feature/target alignment
- Model training and evaluation
- Model persistence
- Registry operations
- Parameter hash determinism

**Run:**
```bash
pytest backend/tests/test_training_unit.py -v
```

### Integration Tests (`tests/test_training_integration.py`)

**Coverage:**
- End-to-end training with mocked yfinance
- Predict endpoint after training
- Prune endpoint with different policies
- Models list endpoint
- Registry updates
- Archive creation
- Determinism verification

**Run:**
```bash
pytest backend/tests/test_training_integration.py -v
```

## Usage Examples

### Train AAPL with 10-year data (production)
```bash
curl -X POST "http://localhost:8000/api/training/train/AAPL?mode=10y&retain=none&archive=true"
```

### Train TSLA with 5-year data (development)
```bash
curl -X POST "http://localhost:8000/api/training/train/TSLA?mode=5y&retain=window&window_days=180"
```

### Get prediction for AAPL
```bash
curl "http://localhost:8000/api/training/predict/AAPL?mode=10y"
```

### List all trained models
```bash
curl "http://localhost:8000/api/training/models"
```

### Bulk prune to 90-day window
```bash
curl -X POST "http://localhost:8000/api/training/prune?retain=window&window_days=90"
```

## Integration with Research Model

The two models complement each other:

**Research Model** answers: *"Given this article, what's the probability of a positive 3-day return?"*
- Uses article content, LLM analysis, and market context
- Continuously learns from realized outcomes
- Provides confidence levels and interpretations

**Price Prediction Model** answers: *"Based on historical price patterns, what's tomorrow's close price?"*
- Uses only technical indicators from price history
- Periodically retrained on demand
- Provides point forecasts and feature snapshots

**Combined Use Case:**
```python
# Get article-based prediction
research_pred = await fetch("/api/research/predict", {
    "analysis": article_analysis
})

# Get price-based prediction
price_pred = await fetch(f"/api/training/predict/{ticker}?mode=10y")

# Combine signals
if research_pred["prob_up_3d"] > 0.7 and price_pred["predicted_change_pct"] > 1.0:
    # Both models bullish - high confidence signal
    signal = "STRONG_BUY"
```

## Best Practices

1. **Use 10y mode for production** - More robust, better generalization
2. **Use 5y mode for rapid iteration** - Faster training during development
3. **Always use `retain="none"` in production** - Minimize storage
4. **Archive important training runs** - For audit trail and reproducibility
5. **Retrain periodically** - Market conditions change over time
6. **Monitor R² scores** - Declining scores indicate need for retraining
7. **Use walk-forward validation** - Prevents look-ahead bias
8. **Track parameter hashes** - Ensures reproducibility

## Troubleshooting

**Model R² is low (<0.3):**
- Try 10y mode for more training data
- Check if ticker has sufficient history
- Consider if market is in high-volatility regime

**Training fails with "No data available":**
- Verify ticker symbol is correct
- Check yfinance connectivity
- Try different period (5y vs 10y)

**Prediction returns 404:**
- Train model first using `/api/training/train/{ticker}`
- Verify model file exists in `backend/models/`
- Check registry with `/api/training/models`

**Database growing too large:**
- Run `/api/training/prune` with `retain="none"`
- Verify VACUUM is running after pruning
- Check retention policy in training calls

## Future Enhancements

- [ ] Multi-horizon predictions (1D, 5D, 10D)
- [ ] Ensemble models combining 5y and 10y
- [ ] Automated retraining scheduler
- [ ] Model performance monitoring dashboard
- [ ] Feature importance tracking
- [ ] Sector-specific models
- [ ] Volatility forecasting
- [ ] Confidence intervals for predictions

