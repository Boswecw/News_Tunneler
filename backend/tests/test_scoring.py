"""Tests for scoring logic."""
import pytest
from datetime import datetime, timezone, timedelta
from app.core.scoring import (
    score_catalyst,
    score_novelty,
    score_credibility,
    compute_total_score,
)


class TestCatalystScoring:
    """Test catalyst scoring."""

    def test_high_catalyst_keywords(self):
        """Test high catalyst keywords return 5."""
        assert score_catalyst("Company announces 8-K filing", "") == 5.0
        assert score_catalyst("Earnings beat expectations", "") == 5.0
        assert score_catalyst("FDA approval granted", "") == 5.0
        assert score_catalyst("Merger announced", "") == 5.0

    def test_medium_catalyst_keywords(self):
        """Test medium catalyst keywords return 3."""
        assert score_catalyst("Clinical trial results", "") == 3.0
        assert score_catalyst("Partnership announced", "") == 3.0
        assert score_catalyst("License agreement", "") == 3.0

    def test_no_catalyst_keywords(self):
        """Test no catalyst keywords return 0."""
        assert score_catalyst("Regular news update", "") == 0.0


class TestNoveltyScoring:
    """Test novelty scoring."""

    def test_recent_article(self):
        """Test article < 6h old returns 5."""
        now = datetime.now(timezone.utc)
        recent = now - timedelta(hours=3)
        assert score_novelty(recent) == 5.0

    def test_moderately_recent_article(self):
        """Test article < 24h old returns 3."""
        now = datetime.now(timezone.utc)
        moderately_recent = now - timedelta(hours=12)
        assert score_novelty(moderately_recent) == 3.0

    def test_old_article(self):
        """Test article >= 24h old returns 1."""
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=2)
        assert score_novelty(old) == 1.0


class TestCredibilityScoring:
    """Test credibility scoring."""

    def test_high_credibility_domains(self):
        """Test high credibility domains return 5."""
        assert score_credibility("https://sec.gov/cgi-bin/browse-edgar") == 5.0
        assert score_credibility("https://investor.apple.com/news") == 5.0
        assert score_credibility("https://ir.microsoft.com/press-release") == 5.0
        assert score_credibility("https://prnewswire.com/news") == 5.0
        assert score_credibility("https://globenewswire.com/news") == 5.0
        assert score_credibility("https://businesswire.com/news") == 5.0

    def test_low_credibility_domains(self):
        """Test other domains return 3."""
        assert score_credibility("https://example.com/news") == 3.0
        assert score_credibility("https://twitter.com/user") == 3.0


class TestTotalScoreComputation:
    """Test total score computation."""

    def test_default_weights(self):
        """Test total score with default weights."""
        total = compute_total_score(5.0, 5.0, 5.0, 4.0, 0.0)
        assert total == 19.0

    def test_custom_weights(self):
        """Test total score with custom weights."""
        weights = {
            "catalyst": 2.0,
            "novelty": 1.0,
            "credibility": 1.0,
            "sentiment": 1.0,
            "liquidity": 1.0,
        }
        total = compute_total_score(5.0, 5.0, 5.0, 4.0, 0.0, weights)
        assert total == 24.0  # 5*2 + 5 + 5 + 4 + 0

