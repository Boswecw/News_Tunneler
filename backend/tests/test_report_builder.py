"""
Unit tests for report_builder.py

Tests:
- Composite score calculation
- Filtering and bucketing (buys/sells)
- Empty opportunities handling
- Market snapshot calculation
"""
import pytest
from datetime import datetime, timedelta
from app.services.report_builder import (
    compute_composite_score,
    apply_filters,
    build_market_snapshot,
)


class TestCompositeScore:
    """Test composite score calculation."""
    
    def test_perfect_score(self):
        """Test maximum composite score."""
        score = compute_composite_score(
            confidence=1.0,
            expected_return_pct=10.0,
            r2_score=1.0
        )
        # (0.4 * 1.0) + (0.4 * 10.0 / 10.0) + (0.2 * 1.0) = 0.4 + 0.4 + 0.2 = 1.0
        assert score == pytest.approx(1.0, abs=0.01)
    
    def test_zero_score(self):
        """Test minimum composite score."""
        score = compute_composite_score(
            confidence=0.0,
            expected_return_pct=0.0,
            r2_score=0.0
        )
        assert score == pytest.approx(0.0, abs=0.01)
    
    def test_typical_score(self):
        """Test typical composite score."""
        score = compute_composite_score(
            confidence=0.75,
            expected_return_pct=3.5,
            r2_score=0.96
        )
        # (0.4 * 0.75) + (0.4 * 3.5 / 10.0) + (0.2 * 0.96)
        # = 0.3 + 0.14 + 0.192 = 0.632
        assert score == pytest.approx(0.632, abs=0.01)
    
    def test_negative_return(self):
        """Test that negative returns use absolute value."""
        score = compute_composite_score(
            confidence=0.80,
            expected_return_pct=-4.0,
            r2_score=0.95
        )
        # (0.4 * 0.80) + (0.4 * 4.0 / 10.0) + (0.2 * 0.95)
        # = 0.32 + 0.16 + 0.19 = 0.67
        assert score == pytest.approx(0.67, abs=0.01)


class TestFiltering:
    """Test filtering and bucketing logic."""
    
    def test_split_buys_sells(self):
        """Test that opportunities are correctly split into buys and sells."""
        opportunities = [
            {
                "symbol": "TSLA",
                "llm_stance": "BULLISH",
                "llm_confidence": 0.85,
                "expected_return_pct": 3.5,
                "model_r2": 0.96,
                "composite_score": 0.70,
                "rsi": 45.0,
            },
            {
                "symbol": "AAPL",
                "llm_stance": "BEARISH",
                "llm_confidence": 0.80,
                "expected_return_pct": -2.5,
                "model_r2": 0.97,
                "composite_score": 0.65,
                "rsi": 65.0,
            },
            {
                "symbol": "MSFT",
                "llm_stance": "BULLISH",
                "llm_confidence": 0.75,
                "expected_return_pct": 2.0,
                "model_r2": 0.95,
                "composite_score": 0.60,
                "rsi": 50.0,
            },
        ]
        
        buys, sells = apply_filters(
            opportunities,
            min_confidence=0.70,
            min_expected_return_pct=1.0,
            min_r2=0.95,
            max_per_side=10
        )
        
        assert len(buys) == 2
        assert len(sells) == 1
        assert buys[0]["symbol"] == "TSLA"  # Highest composite score
        assert sells[0]["symbol"] == "AAPL"
    
    def test_filter_by_confidence(self):
        """Test filtering by minimum confidence."""
        opportunities = [
            {
                "symbol": "TSLA",
                "llm_stance": "BULLISH",
                "llm_confidence": 0.85,
                "expected_return_pct": 3.5,
                "model_r2": 0.96,
                "composite_score": 0.70,
                "rsi": 45.0,
            },
            {
                "symbol": "AAPL",
                "llm_stance": "BULLISH",
                "llm_confidence": 0.65,  # Below threshold
                "expected_return_pct": 2.5,
                "model_r2": 0.97,
                "composite_score": 0.60,
                "rsi": 50.0,
            },
        ]
        
        buys, sells = apply_filters(
            opportunities,
            min_confidence=0.70,
            min_expected_return_pct=1.0,
            min_r2=0.95,
            max_per_side=10
        )
        
        assert len(buys) == 1
        assert buys[0]["symbol"] == "TSLA"
    
    def test_filter_by_expected_return(self):
        """Test filtering by minimum expected return."""
        opportunities = [
            {
                "symbol": "TSLA",
                "llm_stance": "BULLISH",
                "llm_confidence": 0.85,
                "expected_return_pct": 3.5,
                "model_r2": 0.96,
                "composite_score": 0.70,
                "rsi": 45.0,
            },
            {
                "symbol": "AAPL",
                "llm_stance": "BULLISH",
                "llm_confidence": 0.80,
                "expected_return_pct": 0.5,  # Below threshold
                "model_r2": 0.97,
                "composite_score": 0.60,
                "rsi": 50.0,
            },
        ]
        
        buys, sells = apply_filters(
            opportunities,
            min_confidence=0.70,
            min_expected_return_pct=1.0,
            min_r2=0.95,
            max_per_side=10
        )
        
        assert len(buys) == 1
        assert buys[0]["symbol"] == "TSLA"
    
    def test_max_per_side_limit(self):
        """Test that max_per_side limits results."""
        opportunities = [
            {
                "symbol": f"TICK{i}",
                "llm_stance": "BULLISH",
                "llm_confidence": 0.80,
                "expected_return_pct": 2.0,
                "model_r2": 0.96,
                "composite_score": 0.70 - (i * 0.01),
                "rsi": 50.0,
            }
            for i in range(15)
        ]
        
        buys, sells = apply_filters(
            opportunities,
            min_confidence=0.70,
            min_expected_return_pct=1.0,
            min_r2=0.95,
            max_per_side=8
        )
        
        assert len(buys) <= 8
    
    def test_empty_opportunities(self):
        """Test handling of empty opportunities list."""
        buys, sells = apply_filters(
            [],
            min_confidence=0.70,
            min_expected_return_pct=1.0,
            min_r2=0.95,
            max_per_side=10
        )
        
        assert len(buys) == 0
        assert len(sells) == 0


class TestMarketSnapshot:
    """Test market snapshot calculation."""
    
    def test_bullish_mood(self):
        """Test bullish market mood calculation."""
        opportunities = [
            {"llm_stance": "BULLISH", "article_title": "Tesla soars"},
            {"llm_stance": "BULLISH", "article_title": "Apple beats earnings"},
            {"llm_stance": "NEUTRAL", "article_title": "Market update"},
        ]
        
        snapshot = build_market_snapshot(opportunities)
        
        assert snapshot["market_mood"] == "Bullish"
        assert len(snapshot["notable_catalysts"]) > 0
    
    def test_bearish_mood(self):
        """Test bearish market mood calculation."""
        opportunities = [
            {"llm_stance": "BEARISH", "article_title": "Tesla drops"},
            {"llm_stance": "BEARISH", "article_title": "Apple misses"},
            {"llm_stance": "NEUTRAL", "article_title": "Market update"},
        ]
        
        snapshot = build_market_snapshot(opportunities)
        
        assert snapshot["market_mood"] == "Bearish"
    
    def test_neutral_mood(self):
        """Test neutral market mood calculation."""
        opportunities = [
            {"llm_stance": "BULLISH", "article_title": "Tesla up"},
            {"llm_stance": "BEARISH", "article_title": "Apple down"},
        ]
        
        snapshot = build_market_snapshot(opportunities)
        
        assert snapshot["market_mood"] == "Neutral"
    
    def test_empty_snapshot(self):
        """Test snapshot with no opportunities."""
        snapshot = build_market_snapshot([])
        
        assert snapshot["market_mood"] == "Neutral"
        assert snapshot["notable_catalysts"] == []
        assert snapshot["confidence_range"] == "N/A"

