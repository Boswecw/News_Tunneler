"""
Feature engineering for trading signals.

Adds technical indicators, sentiment aggregation, temporal features,
and interaction features to improve model performance.
"""
import logging
from datetime import datetime
from typing import Dict, List
import pandas as pd
import numpy as np
import yfinance as yf
from ta import add_all_ta_features
from ta.utils import dropna

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Feature engineering for trading signals.
    """
    
    def __init__(self):
        """Initialize feature engineer."""
        pass
    
    def add_technical_indicators(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> Dict[str, float]:
        """
        Add technical indicators using yfinance and ta library.
        
        Args:
            symbol: Ticker symbol
            period: Data period (1mo, 3mo, 6mo, 1y)
            interval: Data interval (1d, 1h, etc.)
            
        Returns:
            Dict of technical indicator features
        """
        try:
            # Get historical data
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty or len(df) < 20:
                logger.warning(f"Insufficient data for {symbol}")
                return self._get_default_technical_features()
            
            # Clean data
            df = dropna(df)
            
            # Add all technical indicators
            df = add_all_ta_features(
                df,
                open="Open",
                high="High",
                low="Low",
                close="Close",
                volume="Volume",
                fillna=True
            )
            
            # Extract latest values
            latest = df.iloc[-1]
            
            # RSI (Relative Strength Index)
            rsi = latest.get('momentum_rsi', 50.0)
            
            # MACD
            macd = latest.get('trend_macd', 0.0)
            macd_signal = latest.get('trend_macd_signal', 0.0)
            macd_diff = latest.get('trend_macd_diff', 0.0)
            
            # Bollinger Bands
            bb_high = latest.get('volatility_bbh', 0.0)
            bb_low = latest.get('volatility_bbl', 0.0)
            bb_mid = latest.get('volatility_bbm', 0.0)
            close = latest.get('Close', 0.0)
            
            # BB position (0 = at lower band, 1 = at upper band)
            if bb_high != bb_low:
                bb_position = (close - bb_low) / (bb_high - bb_low)
            else:
                bb_position = 0.5
            
            # ATR (Average True Range)
            atr = latest.get('volatility_atr', 0.0)
            atr_pct = (atr / close * 100) if close > 0 else 0.0
            
            # ADX (Average Directional Index)
            adx = latest.get('trend_adx', 0.0)
            
            # OBV (On-Balance Volume)
            obv = latest.get('volume_obv', 0.0)
            
            # Stochastic Oscillator
            stoch = latest.get('momentum_stoch', 50.0)
            stoch_signal = latest.get('momentum_stoch_signal', 50.0)
            
            # CCI (Commodity Channel Index)
            cci = latest.get('trend_cci', 0.0)
            
            # Williams %R
            williams_r = latest.get('momentum_wr', -50.0)
            
            return {
                'rsi': float(rsi),
                'macd': float(macd),
                'macd_signal': float(macd_signal),
                'macd_diff': float(macd_diff),
                'bb_position': float(bb_position),
                'atr_pct': float(atr_pct),
                'adx': float(adx),
                'obv': float(obv),
                'stoch': float(stoch),
                'stoch_signal': float(stoch_signal),
                'cci': float(cci),
                'williams_r': float(williams_r),
            }
        
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {e}")
            return self._get_default_technical_features()
    
    def _get_default_technical_features(self) -> Dict[str, float]:
        """Get default technical features when calculation fails."""
        return {
            'rsi': 50.0,
            'macd': 0.0,
            'macd_signal': 0.0,
            'macd_diff': 0.0,
            'bb_position': 0.5,
            'atr_pct': 3.0,
            'adx': 25.0,
            'obv': 0.0,
            'stoch': 50.0,
            'stoch_signal': 50.0,
            'cci': 0.0,
            'williams_r': -50.0,
        }
    
    def add_sentiment_aggregation(
        self,
        sentiment: float,
        magnitude: float,
        credibility: float
    ) -> Dict[str, float]:
        """
        Create aggregated sentiment features.
        
        Args:
            sentiment: Raw sentiment score
            magnitude: Magnitude score
            credibility: Credibility score
            
        Returns:
            Dict of aggregated sentiment features
        """
        # Weighted sentiment (credibility-weighted)
        weighted_sentiment = sentiment * (credibility / 5.0)
        
        # Sentiment strength (sentiment * magnitude)
        sentiment_strength = sentiment * magnitude
        
        # Credible sentiment (sentiment * credibility)
        credible_sentiment = sentiment * credibility
        
        # Sentiment momentum (placeholder - would need historical data)
        sentiment_momentum = 0.0
        
        return {
            'weighted_sentiment': float(weighted_sentiment),
            'sentiment_strength': float(sentiment_strength),
            'credible_sentiment': float(credible_sentiment),
            'sentiment_momentum': float(sentiment_momentum),
        }
    
    def add_temporal_features(self, timestamp: datetime = None) -> Dict[str, float]:
        """
        Add temporal features (day of week, hour, etc.).
        
        Args:
            timestamp: Timestamp to extract features from (uses current time if None)
            
        Returns:
            Dict of temporal features
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Day of week (0 = Monday, 6 = Sunday)
        day_of_week = timestamp.weekday()
        
        # Hour of day (0-23)
        hour_of_day = timestamp.hour
        
        # Is market hours (9:30 AM - 4:00 PM ET, simplified to 14:30-21:00 UTC)
        is_market_hours = 1.0 if 14 <= hour_of_day < 21 else 0.0
        
        # Is pre-market (4:00 AM - 9:30 AM ET, simplified to 9:00-14:30 UTC)
        is_premarket = 1.0 if 9 <= hour_of_day < 14 else 0.0
        
        # Is after-hours (4:00 PM - 8:00 PM ET, simplified to 21:00-1:00 UTC)
        is_afterhours = 1.0 if hour_of_day >= 21 or hour_of_day < 1 else 0.0
        
        # Is weekend
        is_weekend = 1.0 if day_of_week >= 5 else 0.0
        
        # Is Monday (often volatile)
        is_monday = 1.0 if day_of_week == 0 else 0.0
        
        # Is Friday (often profit-taking)
        is_friday = 1.0 if day_of_week == 4 else 0.0
        
        return {
            'day_of_week': float(day_of_week),
            'hour_of_day': float(hour_of_day),
            'is_market_hours': float(is_market_hours),
            'is_premarket': float(is_premarket),
            'is_afterhours': float(is_afterhours),
            'is_weekend': float(is_weekend),
            'is_monday': float(is_monday),
            'is_friday': float(is_friday),
        }
    
    def add_interaction_features(self, features: Dict) -> Dict[str, float]:
        """
        Create interaction features between existing features.
        
        Args:
            features: Dict of existing features
            
        Returns:
            Dict of interaction features
        """
        interactions = {}
        
        # Sentiment * Volatility
        if 'sentiment' in features and 'vol_z' in features:
            interactions['sentiment_x_vol'] = features['sentiment'] * features['vol_z']
        
        # Sentiment * Momentum
        if 'sentiment' in features and 'ret_1d' in features:
            interactions['sentiment_x_momentum'] = features['sentiment'] * features['ret_1d']
        
        # Novelty * Credibility
        if 'novelty' in features and 'credibility' in features:
            interactions['novelty_x_credibility'] = features['novelty'] * features['credibility']
        
        # RSI * Sentiment
        if 'rsi' in features and 'sentiment' in features:
            interactions['rsi_x_sentiment'] = (features['rsi'] - 50) * features['sentiment']
        
        # MACD * Sentiment
        if 'macd_diff' in features and 'sentiment' in features:
            interactions['macd_x_sentiment'] = features['macd_diff'] * features['sentiment']
        
        # Volatility * Gap
        if 'vol_z' in features and 'gap_pct' in features:
            interactions['vol_x_gap'] = features['vol_z'] * features['gap_pct']
        
        return interactions
    
    def engineer_all_features(
        self,
        base_features: Dict,
        symbol: str,
        timestamp: datetime = None
    ) -> Dict:
        """
        Engineer all features for a signal.
        
        Args:
            base_features: Base features from signal
            symbol: Ticker symbol
            timestamp: Signal timestamp
            
        Returns:
            Dict with all engineered features
        """
        # Start with base features
        all_features = base_features.copy()
        
        # Add technical indicators
        technical = self.add_technical_indicators(symbol)
        all_features.update(technical)
        
        # Add sentiment aggregation
        sentiment_agg = self.add_sentiment_aggregation(
            base_features.get('sentiment', 0.0),
            base_features.get('magnitude', 0.0),
            base_features.get('credibility', 0.0)
        )
        all_features.update(sentiment_agg)
        
        # Add temporal features
        temporal = self.add_temporal_features(timestamp)
        all_features.update(temporal)
        
        # Add interaction features
        interactions = self.add_interaction_features(all_features)
        all_features.update(interactions)
        
        return all_features

