"""Predictive model training and inference for next-day price predictions."""
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import numpy as np
from app.core.logging import logger

# Try to import sklearn for simple online learning
try:
    from sklearn.linear_model import SGDRegressor
    from sklearn.preprocessing import StandardScaler
    import pickle
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn not available for predictive training")

# Try to import yfinance for historical data
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not available for predictive training")


MODELS_DIR = Path(__file__).parent.parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)


class PredictiveModel:
    """Simple online learning model for price prediction."""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.model = None
        self.scaler = None
        self.last_price = None
        self.model_path = MODELS_DIR / f"{symbol}_model.pkl"
        self.scaler_path = MODELS_DIR / f"{symbol}_scaler.pkl"
        
        if SKLEARN_AVAILABLE:
            self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Load existing model or create new one."""
        if self.model_path.exists() and self.scaler_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                logger.info(f"Loaded existing model for {self.symbol}")
            except Exception as e:
                logger.error(f"Error loading model for {self.symbol}: {e}")
                self._create_new_model()
        else:
            self._create_new_model()
    
    def _create_new_model(self):
        """Create new SGD regressor model."""
        self.model = SGDRegressor(
            loss='squared_error',
            penalty='l2',
            alpha=0.0001,
            learning_rate='adaptive',
            eta0=0.01,
            max_iter=1000,
            tol=1e-3,
            random_state=42
        )
        self.scaler = StandardScaler()
        logger.info(f"Created new model for {self.symbol}")
    
    def save(self):
        """Save model and scaler to disk."""
        if not SKLEARN_AVAILABLE:
            return
        
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            logger.info(f"Saved model for {self.symbol}")
        except Exception as e:
            logger.error(f"Error saving model for {self.symbol}: {e}")
    
    def train_on_intraday(self, data_points: List[Dict]) -> bool:
        """
        Train model on intraday data points.
        
        Args:
            data_points: List of {t: timestamp_ms, v: price, ...}
        
        Returns:
            True if training successful
        """
        if not SKLEARN_AVAILABLE or not data_points:
            return False
        
        try:
            # Extract features and targets
            X = []
            y = []
            
            for i in range(len(data_points) - 1):
                point = data_points[i]
                next_point = data_points[i + 1]
                
                # Convert timestamp to minute of day (0-1439)
                dt = datetime.fromtimestamp(point["t"] / 1000, tz=ZoneInfo("America/New_York"))
                minute_of_day = dt.hour * 60 + dt.minute
                
                # Features: minute of day, current price, price change from previous
                price = point["v"]
                if i > 0:
                    prev_price = data_points[i - 1]["v"]
                    price_change = (price - prev_price) / prev_price if prev_price > 0 else 0
                else:
                    price_change = 0
                
                features = [minute_of_day, price, price_change]
                target = next_point["v"]  # Predict next price
                
                X.append(features)
                y.append(target)
            
            if not X:
                return False
            
            X = np.array(X)
            y = np.array(y)
            
            # Fit scaler if not fitted
            if not hasattr(self.scaler, 'mean_'):
                self.scaler.fit(X)
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Partial fit (online learning)
            if not hasattr(self.model, 'coef_'):
                # First fit
                self.model.fit(X_scaled, y)
            else:
                # Incremental update
                self.model.partial_fit(X_scaled, y)
            
            # Store last price
            self.last_price = data_points[-1]["v"]
            
            logger.info(f"Trained model for {self.symbol} on {len(X)} samples")
            return True
            
        except Exception as e:
            logger.error(f"Error training model for {self.symbol}: {e}")
            return False
    
    def predict_next_day(self, date: datetime) -> Tuple[List[Dict], List[Dict]]:
        """
        Generate predictions for next trading day.
        
        Args:
            date: Date for predictions (should be next trading day)
        
        Returns:
            Tuple of (predict_line, predict_signals)
            - predict_line: List of {symbol, ts, value}
            - predict_signals: List of {symbol, ts, signal, prob, price}
        """
        if not SKLEARN_AVAILABLE or not hasattr(self.model, 'coef_'):
            return [], []
        
        if self.last_price is None:
            logger.warning(f"No last price for {self.symbol}, cannot predict")
            return [], []
        
        try:
            predict_line = []
            predict_signals = []
            
            # Market hours: 9:30 AM - 4:00 PM ET (570 - 960 minutes)
            et_tz = ZoneInfo("America/New_York")
            market_open = date.replace(hour=9, minute=30, second=0, microsecond=0, tzinfo=et_tz)
            
            current_price = self.last_price
            prev_price = current_price
            
            # Generate predictions for each minute
            for minute in range(570, 960):  # 9:30 AM to 4:00 PM
                # Calculate timestamp
                minutes_from_open = minute - 570
                prediction_time = market_open + timedelta(minutes=minutes_from_open)
                ts_ms = int(prediction_time.timestamp() * 1000)
                
                # Prepare features
                price_change = (current_price - prev_price) / prev_price if prev_price > 0 else 0
                features = np.array([[minute, current_price, price_change]])
                
                # Scale and predict
                features_scaled = self.scaler.transform(features)
                predicted_price = self.model.predict(features_scaled)[0]
                
                # Apply some randomness and constraints
                # Add small drift to make it more realistic
                drift = np.random.uniform(-0.20, 0.20)
                predicted_price = max(0.01, predicted_price + drift)
                
                # Add to prediction line
                predict_line.append({
                    "symbol": self.symbol,
                    "ts": ts_ms,
                    "value": round(predicted_price, 2)
                })
                
                # Generate signals based on price movement
                price_change_pct = (predicted_price - current_price) / current_price if current_price > 0 else 0
                
                # BUY signal if predicted to go up significantly
                if price_change_pct > 0.002:  # 0.2% increase
                    prob = min(0.95, 0.5 + price_change_pct * 10)
                    predict_signals.append({
                        "symbol": self.symbol,
                        "ts": ts_ms,
                        "signal": "BUY",
                        "prob": round(prob, 2),
                        "price": round(predicted_price, 2)
                    })
                
                # SELL signal if predicted to go down significantly
                elif price_change_pct < -0.002:  # 0.2% decrease
                    prob = min(0.95, 0.5 + abs(price_change_pct) * 10)
                    predict_signals.append({
                        "symbol": self.symbol,
                        "ts": ts_ms,
                        "signal": "SELL",
                        "prob": round(prob, 2),
                        "price": round(predicted_price, 2)
                    })
                
                # Update for next iteration
                prev_price = current_price
                current_price = predicted_price
            
            logger.info(f"Generated {len(predict_line)} predictions and {len(predict_signals)} signals for {self.symbol}")
            return predict_line, predict_signals
            
        except Exception as e:
            logger.error(f"Error generating predictions for {self.symbol}: {e}")
            return [], []


def train_symbol(symbol: str, intraday_data: Optional[List[Dict]] = None) -> bool:
    """
    Train model for a symbol and generate predictions.
    
    Args:
        symbol: Stock ticker symbol
        intraday_data: Optional intraday data. If None, will fetch from yfinance
    
    Returns:
        True if successful
    """
    if not SKLEARN_AVAILABLE:
        logger.warning("sklearn not available, skipping training")
        return False
    
    try:
        # Fetch intraday data if not provided
        if intraday_data is None:
            if not YFINANCE_AVAILABLE:
                logger.warning(f"yfinance not available, cannot fetch data for {symbol}")
                return False
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1d", interval="1m")
            
            if df.empty:
                logger.warning(f"No intraday data for {symbol}")
                return False
            
            # Convert to data points
            intraday_data = []
            for idx, row in df.iterrows():
                intraday_data.append({
                    "t": int(idx.timestamp() * 1000),
                    "v": round(float(row['Close']), 2),
                })
        
        if not intraday_data:
            logger.warning(f"No data to train for {symbol}")
            return False
        
        # Create and train model
        model = PredictiveModel(symbol)
        success = model.train_on_intraday(intraday_data)
        
        if not success:
            return False
        
        # Save model
        model.save()
        
        # Generate predictions for next trading day
        et_tz = ZoneInfo("America/New_York")
        now_et = datetime.now(et_tz)
        
        # Find next trading day (skip weekends)
        next_day = now_et + timedelta(days=1)
        while next_day.weekday() >= 5:  # Saturday=5, Sunday=6
            next_day += timedelta(days=1)
        
        predict_line, predict_signals = model.predict_next_day(next_day)
        
        # Save predictions
        line_path = MODELS_DIR / f"{symbol}_predict_line.json"
        signals_path = MODELS_DIR / f"{symbol}_predict_signals.json"
        
        with open(line_path, 'w') as f:
            json.dump(predict_line, f)
        
        with open(signals_path, 'w') as f:
            json.dump(predict_signals, f)
        
        logger.info(f"Successfully trained and generated predictions for {symbol}")
        return True
        
    except Exception as e:
        logger.error(f"Error in train_symbol for {symbol}: {e}")
        return False

