# Phase 3 Implementation Plan - ML Enhancements

**Date:** October 29, 2025  
**Status:** 🚀 **STARTING**  
**Duration:** 2-3 weeks (estimated)  
**Prerequisites:** ✅ Phase 1 & 2 Complete

---

## 📊 Overview

Phase 3 focuses on **ML Enhancements** to improve prediction accuracy and add advanced analytics capabilities:

1. **Advanced ML Models** (1 week) - Random Forest, XGBoost, ensemble methods
2. **FinBERT Sentiment** (3 days) - Financial-specific sentiment analysis
3. **Time-Series Forecasting** (1 week) - Prophet for price prediction
4. **Feature Engineering** (2 days) - Advanced features and explainability

---

## 🎯 Component 1: Advanced ML Models

### Current State
- Simple logistic regression in `backend/app/train/train.py`
- Limited predictive power (~60% accuracy)
- No model versioning or A/B testing
- No feature importance analysis

### Target State
- Ensemble of models (Random Forest, XGBoost, Gradient Boosting)
- Cross-validation and hyperparameter tuning
- Model versioning with performance tracking
- SHAP values for explainability
- A/B testing framework

### Implementation Steps

#### Step 1: Create Advanced Model Training Module
**File:** `backend/app/ml/advanced_models.py`

**Features:**
- Multiple model types (Random Forest, XGBoost, Gradient Boosting)
- Cross-validation with stratified K-fold
- Hyperparameter tuning with GridSearchCV
- Model comparison and selection
- Model persistence with versioning

**Estimated Time:** 1 day

---

#### Step 2: Add Feature Engineering
**File:** `backend/app/ml/feature_engineering.py`

**Features:**
- Technical indicators (RSI, MACD, Bollinger Bands)
- Sentiment aggregation features
- Temporal features (day of week, time of day)
- Interaction features
- Feature scaling and normalization

**Estimated Time:** 1 day

---

#### Step 3: Implement Model Explainability
**File:** `backend/app/ml/explainability.py`

**Features:**
- SHAP values for feature importance
- Partial dependence plots
- Feature contribution analysis
- Model interpretation API endpoints

**Estimated Time:** 1 day

---

#### Step 4: Add Model Versioning
**File:** `backend/app/ml/model_registry.py`

**Features:**
- Model metadata tracking (version, metrics, timestamp)
- Model comparison dashboard
- A/B testing framework
- Automatic model selection based on performance

**Estimated Time:** 1 day

---

#### Step 5: Create Training Pipeline
**File:** `backend/app/ml/training_pipeline.py`

**Features:**
- Automated data collection
- Feature engineering pipeline
- Model training and evaluation
- Model deployment
- Celery task for scheduled retraining

**Estimated Time:** 1 day

---

## 🎯 Component 2: FinBERT Sentiment Analysis

### Current State
- VADER sentiment only (rule-based)
- Limited accuracy for financial text
- No context understanding
- Simple positive/negative/neutral classification

### Target State
- FinBERT transformer model (finance-specific)
- Combined VADER + FinBERT scoring
- Confidence scores
- Batch processing with Celery
- Caching for performance

### Implementation Steps

#### Step 1: Install FinBERT Dependencies
**Dependencies:**
- `transformers>=4.30.0`
- `torch>=2.0.0`
- `sentencepiece>=0.1.99`

**Estimated Time:** 30 minutes

---

#### Step 2: Create FinBERT Sentiment Module
**File:** `backend/app/core/sentiment_advanced.py`

**Features:**
- FinBERT model loading with caching
- Combined VADER + FinBERT analysis
- Confidence scoring
- Batch processing support
- Fallback to VADER on errors

**Estimated Time:** 1 day

---

#### Step 3: Add Celery Task for Batch Processing
**File:** `backend/app/tasks/sentiment_tasks.py`

**Features:**
- Async FinBERT analysis
- Batch article processing
- Progress tracking
- Error handling and retries

**Estimated Time:** 4 hours

---

#### Step 4: Update Scoring System
**File:** `backend/app/core/scoring.py` (modify)

**Features:**
- Use combined sentiment score
- Weight FinBERT higher than VADER
- Add confidence to scoring
- Update API responses

**Estimated Time:** 4 hours

---

#### Step 5: Add Feature Flag
**Feature Flag:** `FINBERT_SENTIMENT`

**Features:**
- Gradual rollout capability
- A/B testing VADER vs FinBERT
- Performance monitoring

**Estimated Time:** 1 hour

---

## 🎯 Component 3: Time-Series Forecasting

### Current State
- No price forecasting
- Static predictions
- No temporal modeling

### Target State
- Prophet for multi-day price forecasting
- ARIMA for trend analysis
- Volatility forecasting
- Integration with signals

### Implementation Steps

#### Step 1: Install Forecasting Dependencies
**Dependencies:**
- `prophet>=1.1.5`
- `statsmodels>=0.14.0`
- `pmdarima>=2.0.4` (auto-ARIMA)

**Estimated Time:** 30 minutes

---

#### Step 2: Create Forecasting Module
**File:** `backend/app/ml/forecasting.py`

**Features:**
- Prophet price forecasting
- ARIMA trend analysis
- Volatility forecasting
- Confidence intervals
- Multi-day predictions

**Estimated Time:** 2 days

---

#### Step 3: Add Forecasting API Endpoints
**File:** `backend/app/api/forecasting.py`

**Endpoints:**
- `GET /api/forecast/{symbol}` - Get price forecast
- `GET /api/forecast/{symbol}/volatility` - Get volatility forecast
- `GET /api/forecast/batch` - Batch forecasting

**Estimated Time:** 1 day

---

#### Step 4: Integrate with Signals
**File:** `backend/app/core/scoring.py` (modify)

**Features:**
- Add forecast score to signals
- Weight positive forecasts higher
- Add forecast confidence to metadata

**Estimated Time:** 4 hours

---

#### Step 5: Add Celery Task for Scheduled Forecasting
**File:** `backend/app/tasks/forecast_tasks.py`

**Features:**
- Daily forecast updates
- Batch processing for all active symbols
- Cache forecast results
- Error handling

**Estimated Time:** 4 hours

---

## 🎯 Component 4: Feature Engineering & Explainability

### Implementation Steps

#### Step 1: Add Technical Indicators
**File:** `backend/app/ml/technical_indicators.py`

**Features:**
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Volume indicators
- Momentum indicators

**Estimated Time:** 1 day

---

#### Step 2: Add SHAP Explainability
**File:** `backend/app/ml/explainability.py`

**Features:**
- SHAP value calculation
- Feature importance ranking
- Contribution analysis
- Visualization data for frontend

**Estimated Time:** 1 day

---

## 📦 Dependencies to Add

```txt
# Phase 3 - ML Enhancements
scikit-learn>=1.3.0
xgboost>=2.0.0
lightgbm>=4.0.0
transformers>=4.30.0
torch>=2.0.0
sentencepiece>=0.1.99
prophet>=1.1.5
statsmodels>=0.14.0
pmdarima>=2.0.4
shap>=0.43.0
ta>=0.11.0  # Technical analysis library
```

---

## 📊 Database Schema Updates

### New Table: `ml_models`
```sql
CREATE TABLE ml_models (
    id SERIAL PRIMARY KEY,
    version VARCHAR NOT NULL UNIQUE,
    model_type VARCHAR NOT NULL,  -- 'random_forest', 'xgboost', etc.
    model_path VARCHAR NOT NULL,
    metrics JSON NOT NULL,  -- accuracy, precision, recall, f1, auc
    feature_importance JSON,
    hyperparameters JSON,
    training_samples INTEGER,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### New Table: `forecasts`
```sql
CREATE TABLE forecasts (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR NOT NULL,
    forecast_date DATE NOT NULL,
    predicted_price FLOAT NOT NULL,
    lower_bound FLOAT NOT NULL,
    upper_bound FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    model_version VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    UNIQUE(symbol, forecast_date, model_version)
);
```

---

## 🧪 Testing Strategy

### Unit Tests
- Test each ML model independently
- Test feature engineering functions
- Test FinBERT sentiment analysis
- Test forecasting functions

### Integration Tests
- Test end-to-end training pipeline
- Test model versioning and selection
- Test API endpoints
- Test Celery tasks

### Performance Tests
- Benchmark FinBERT vs VADER
- Measure model inference time
- Test batch processing performance
- Monitor memory usage

---

## 📈 Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Prediction Accuracy | ~60% | >75% | Cross-validation AUC |
| Sentiment Accuracy | ~65% | >80% | Manual validation |
| Forecast MAE | N/A | <5% | Mean Absolute Error |
| Inference Time | <100ms | <200ms | P95 latency |
| Model Explainability | None | SHAP values | Feature importance |

---

## 🚀 Implementation Order

### Week 1: Advanced ML Models
- Day 1-2: Feature engineering + advanced models
- Day 3: Model explainability (SHAP)
- Day 4: Model versioning and registry
- Day 5: Training pipeline + Celery tasks

### Week 2: FinBERT Sentiment
- Day 1-2: FinBERT integration + testing
- Day 3: Batch processing + Celery tasks
- Day 4: Update scoring system
- Day 5: Performance optimization + caching

### Week 3: Time-Series Forecasting
- Day 1-2: Prophet forecasting implementation
- Day 3: ARIMA trend analysis
- Day 4: API endpoints + integration
- Day 5: Celery tasks + testing

---

## 🎯 Phase 3 Checklist

### Advanced ML Models
- [ ] Create `backend/app/ml/advanced_models.py`
- [ ] Create `backend/app/ml/feature_engineering.py`
- [ ] Create `backend/app/ml/explainability.py`
- [ ] Create `backend/app/ml/model_registry.py`
- [ ] Create `backend/app/ml/training_pipeline.py`
- [ ] Add Celery task for model training
- [ ] Create database migration for `ml_models` table
- [ ] Add API endpoints for model management
- [ ] Write unit tests
- [ ] Write integration tests

### FinBERT Sentiment
- [ ] Install dependencies (transformers, torch)
- [ ] Create `backend/app/core/sentiment_advanced.py`
- [ ] Create `backend/app/tasks/sentiment_tasks.py`
- [ ] Update `backend/app/core/scoring.py`
- [ ] Add feature flag `FINBERT_SENTIMENT`
- [ ] Add caching for FinBERT results
- [ ] Write unit tests
- [ ] Performance benchmarking

### Time-Series Forecasting
- [ ] Install dependencies (prophet, statsmodels)
- [ ] Create `backend/app/ml/forecasting.py`
- [ ] Create `backend/app/api/forecasting.py`
- [ ] Create `backend/app/tasks/forecast_tasks.py`
- [ ] Create database migration for `forecasts` table
- [ ] Integrate with scoring system
- [ ] Add Celery Beat schedule
- [ ] Write unit tests
- [ ] Write integration tests

### Documentation
- [ ] Update README with ML features
- [ ] Create ML model documentation
- [ ] Create API documentation for new endpoints
- [ ] Create deployment guide for ML models
- [ ] Create PHASE3_COMPLETION_REPORT.md

---

## 📝 Notes

- FinBERT requires ~500MB model download on first run
- Prophet may require additional system dependencies (pystan)
- XGBoost and LightGBM may need compilation on some systems
- Consider GPU support for faster FinBERT inference
- Monitor memory usage with multiple ML models loaded

---

**Ready to begin Phase 3 implementation!** 🚀

