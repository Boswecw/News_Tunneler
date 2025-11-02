"""
Integration tests for mailer.py report functionality

Tests:
- Email rendering (HTML and text)
- Report ID generation
- send_top_opportunities_report with mocked SMTP
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.mailer import (
    render_report_email,
    generate_report_id,
    send_top_opportunities_report,
)


class TestEmailRendering:
    """Test email template rendering."""
    
    def test_render_with_opportunities(self):
        """Test rendering templates with buy/sell opportunities."""
        context = {
            "session_label": "Pre-Market",
            "report_date": "October 31, 2025",
            "report_time": "07:00 AM ET",
            "buys": [
                {
                    "symbol": "TSLA",
                    "expected_return_pct": 3.5,
                    "llm_confidence": 0.85,
                    "ml_confidence": None,
                    "model_r2": 0.96,
                    "rsi": 45.0,
                    "trend": "Above SMA20",
                }
            ],
            "sells": [
                {
                    "symbol": "AAPL",
                    "expected_return_pct": -2.5,
                    "llm_confidence": 0.80,
                    "ml_confidence": None,
                    "model_r2": 0.97,
                    "rsi": 65.0,
                    "trend": "Below SMA20",
                }
            ],
            "total_candidates": 2,
            "market_snapshot": {
                "market_mood": "Neutral",
                "notable_catalysts": ["Tesla announces new model", "Apple beats earnings"],
                "confidence_range": "80%–85%",
            },
            "backtest_summary": None,
        }
        
        html_content, text_content = render_report_email(context)
        
        # Verify HTML content
        assert "TSLA" in html_content
        assert "AAPL" in html_content
        assert "Pre-Market" in html_content
        assert "October 31, 2025" in html_content
        
        # Verify text content
        assert "TSLA" in text_content
        assert "AAPL" in text_content
        assert "Pre-Market" in text_content
    
    def test_render_empty_opportunities(self):
        """Test rendering templates with no opportunities."""
        context = {
            "session_label": "Mid-Day",
            "report_date": "October 31, 2025",
            "report_time": "12:00 PM ET",
            "buys": [],
            "sells": [],
            "total_candidates": 0,
            "market_snapshot": {
                "market_mood": "Neutral",
                "notable_catalysts": [],
                "confidence_range": "N/A",
            },
            "backtest_summary": None,
        }
        
        html_content, text_content = render_report_email(context)
        
        # Should still render without errors
        assert "Mid-Day" in html_content
        assert "Mid-Day" in text_content
        assert "No buy opportunities" in html_content or "No sell opportunities" in html_content


class TestReportID:
    """Test report ID generation."""
    
    def test_report_id_format(self):
        """Test that report ID has correct format."""
        report_id = generate_report_id("Pre-Market", ["user1@example.com", "user2@example.com"])
        
        # Should be in format: YYYYMMDD_session_hash
        parts = report_id.split("_")
        assert len(parts) == 3
        assert len(parts[0]) == 8  # Date: YYYYMMDD
        assert parts[1] == "pre"  # Session: pre_market
        assert len(parts[2]) == 8  # Hash: 8 chars
    
    def test_report_id_consistency(self):
        """Test that same inputs produce same report ID."""
        recipients = ["user@example.com"]
        
        id1 = generate_report_id("Pre-Market", recipients)
        id2 = generate_report_id("Pre-Market", recipients)
        
        # Should be identical (same date, session, recipients)
        assert id1 == id2
    
    def test_report_id_different_sessions(self):
        """Test that different sessions produce different IDs."""
        recipients = ["user@example.com"]
        
        id1 = generate_report_id("Pre-Market", recipients)
        id2 = generate_report_id("Mid-Day", recipients)
        
        # Should differ in session part
        assert id1 != id2


class TestSendReport:
    """Test send_top_opportunities_report function."""
    
    @patch("app.services.mailer.send_email_smtp")
    @patch("app.services.mailer.build_report_context")
    def test_send_success(self, mock_build_context, mock_send_smtp):
        """Test successful report sending."""
        # Mock report context
        mock_build_context.return_value = {
            "session_label": "Pre-Market",
            "report_date": "October 31, 2025",
            "report_time": "07:00 AM ET",
            "buys": [{"symbol": "TSLA"}],
            "sells": [],
            "total_candidates": 1,
            "market_snapshot": {
                "market_mood": "Bullish",
                "notable_catalysts": [],
                "confidence_range": "85%",
            },
            "backtest_summary": None,
        }
        
        # Mock SMTP sending (no exception = success)
        mock_send_smtp.return_value = None
        
        # Send report
        result = send_top_opportunities_report(
            recipients=["user@example.com"],
            session_label="Pre-Market",
            force=True
        )
        
        # Verify success
        assert result["success"] is True
        assert result["candidates_count"] == 1
        assert result["recipients"] == ["user@example.com"]
        assert "report_id" in result
        
        # Verify SMTP was called
        mock_send_smtp.assert_called_once()
    
    @patch("app.services.mailer.send_email_smtp")
    @patch("app.services.mailer.build_report_context")
    def test_send_empty_opportunities(self, mock_build_context, mock_send_smtp):
        """Test sending report with no opportunities."""
        # Mock empty context
        mock_build_context.return_value = {
            "session_label": "Mid-Day",
            "report_date": "October 31, 2025",
            "report_time": "12:00 PM ET",
            "buys": [],
            "sells": [],
            "total_candidates": 0,
            "market_snapshot": {
                "market_mood": "Neutral",
                "notable_catalysts": [],
                "confidence_range": "N/A",
            },
            "backtest_summary": None,
        }
        
        mock_send_smtp.return_value = None
        
        # Send report
        result = send_top_opportunities_report(
            recipients=["user@example.com"],
            session_label="Mid-Day",
            force=True
        )
        
        # Should still succeed (graceful handling)
        assert result["success"] is True
        assert result["candidates_count"] == 0
    
    @patch("app.services.mailer.send_email_smtp")
    @patch("app.services.mailer.build_report_context")
    def test_send_smtp_failure(self, mock_build_context, mock_send_smtp):
        """Test handling of SMTP failure."""
        # Mock report context
        mock_build_context.return_value = {
            "session_label": "Pre-Market",
            "report_date": "October 31, 2025",
            "report_time": "07:00 AM ET",
            "buys": [],
            "sells": [],
            "total_candidates": 0,
            "market_snapshot": {
                "market_mood": "Neutral",
                "notable_catalysts": [],
                "confidence_range": "N/A",
            },
            "backtest_summary": None,
        }
        
        # Mock SMTP failure
        mock_send_smtp.side_effect = Exception("SMTP connection failed")
        
        # Send report
        result = send_top_opportunities_report(
            recipients=["user@example.com"],
            session_label="Pre-Market",
            force=True
        )
        
        # Should return failure
        assert result["success"] is False
        assert "error" in result
        assert "SMTP connection failed" in result["error"]
    
    @patch("app.services.mailer.check_idempotency")
    @patch("app.services.mailer.send_email_smtp")
    @patch("app.services.mailer.build_report_context")
    def test_idempotency_skip(self, mock_build_context, mock_send_smtp, mock_check_idempotency):
        """Test that idempotency prevents duplicate sends."""
        # Mock idempotency check (already sent)
        mock_check_idempotency.return_value = True
        
        # Send report without force
        result = send_top_opportunities_report(
            recipients=["user@example.com"],
            session_label="Pre-Market",
            force=False
        )
        
        # Should skip sending
        assert result["success"] is True
        assert result.get("skipped") is True
        
        # SMTP should NOT be called
        mock_send_smtp.assert_not_called()
        mock_build_context.assert_not_called()

