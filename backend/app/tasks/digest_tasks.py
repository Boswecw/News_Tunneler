"""
Email Digest Tasks

Celery tasks for sending daily/weekly email digests.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from app.core.celery_app import celery_app
from app.core.structured_logging import get_logger
from app.core.feature_flags import is_feature_enabled, FeatureFlag

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.digest_tasks.send_daily_digest",
    max_retries=2,
    default_retry_delay=600,  # Retry after 10 minutes
)
def send_daily_digest(self) -> Dict[str, Any]:
    """
    Send daily digest email with top signals from the last 24 hours.
    
    Returns:
        Summary of digest sending results
    """
    if not is_feature_enabled(FeatureFlag.EMAIL_DIGESTS):
        logger.warning("Email digests are disabled via feature flag")
        return {
            "sent": 0,
            "error": "Email digests disabled"
        }
    
    try:
        from app.core.db import SessionLocal
        from app.models.signal import Signal
        
        logger.info("Generating daily digest")
        
        db = SessionLocal()
        try:
            # Get top signals from last 24 hours
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            
            top_signals = db.query(Signal).filter(
                Signal.created_at >= cutoff_time
            ).order_by(
                Signal.total_score.desc()
            ).limit(10).all()
            
            logger.info(
                f"Found {len(top_signals)} top signals for daily digest",
                extra={
                    "signal_count": len(top_signals),
                    "cutoff_time": cutoff_time.isoformat(),
                }
            )
            
            if not top_signals:
                logger.info("No signals to include in digest")
                return {
                    "sent": 0,
                    "reason": "No signals found"
                }
            
            # Format digest content
            digest_content = _format_digest(top_signals, "Daily")
            
            # Send email (placeholder - implement actual email sending)
            # For now, just log the digest
            logger.info(
                "Daily digest generated",
                extra={
                    "signal_count": len(top_signals),
                    "top_score": top_signals[0].total_score if top_signals else 0,
                }
            )
            
            # TODO: Implement actual email sending
            # send_email(
            #     to=settings.admin_email,
            #     subject="News Tunneler - Daily Digest",
            #     body=digest_content
            # )
            
            return {
                "sent": 1,
                "signal_count": len(top_signals),
                "top_score": top_signals[0].total_score if top_signals else 0,
            }
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Daily digest failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    name="app.tasks.digest_tasks.send_weekly_digest",
    max_retries=2,
)
def send_weekly_digest(self) -> Dict[str, Any]:
    """
    Send weekly digest email with top signals from the last 7 days.
    
    Returns:
        Summary of digest sending results
    """
    if not is_feature_enabled(FeatureFlag.EMAIL_DIGESTS):
        logger.warning("Email digests are disabled via feature flag")
        return {
            "sent": 0,
            "error": "Email digests disabled"
        }
    
    try:
        from app.core.db import SessionLocal
        from app.models.signal import Signal
        
        logger.info("Generating weekly digest")
        
        db = SessionLocal()
        try:
            # Get top signals from last 7 days
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)
            
            top_signals = db.query(Signal).filter(
                Signal.created_at >= cutoff_time
            ).order_by(
                Signal.total_score.desc()
            ).limit(20).all()
            
            logger.info(
                f"Found {len(top_signals)} top signals for weekly digest",
                extra={
                    "signal_count": len(top_signals),
                    "cutoff_time": cutoff_time.isoformat(),
                }
            )
            
            if not top_signals:
                logger.info("No signals to include in digest")
                return {
                    "sent": 0,
                    "reason": "No signals found"
                }
            
            # Format digest content
            digest_content = _format_digest(top_signals, "Weekly")
            
            # Send email (placeholder)
            logger.info(
                "Weekly digest generated",
                extra={
                    "signal_count": len(top_signals),
                    "top_score": top_signals[0].total_score if top_signals else 0,
                }
            )
            
            return {
                "sent": 1,
                "signal_count": len(top_signals),
                "top_score": top_signals[0].total_score if top_signals else 0,
            }
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Weekly digest failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    name="app.tasks.digest_tasks.send_alert",
    max_retries=3,
    default_retry_delay=60,
)
def send_alert(self, signal_id: int, alert_type: str = "high_score") -> Dict[str, Any]:
    """
    Send immediate alert for high-priority signals.
    
    Args:
        signal_id: ID of the signal to alert on
        alert_type: Type of alert (high_score, breaking_news, etc.)
        
    Returns:
        Alert sending result
    """
    try:
        from app.core.db import SessionLocal
        from app.models.signal import Signal
        
        logger.info(f"Sending alert for signal {signal_id} (type: {alert_type})")
        
        db = SessionLocal()
        try:
            signal = db.query(Signal).filter(Signal.id == signal_id).first()
            if not signal:
                logger.warning(f"Signal not found: {signal_id}")
                return {"error": "Signal not found"}
            
            # Format alert message
            alert_message = f"""
            🚨 News Tunneler Alert - {alert_type.upper()}
            
            Ticker: {signal.ticker}
            Score: {signal.total_score:.2f}
            Title: {signal.title}
            
            Catalyst: {signal.catalyst_score:.2f}
            Novelty: {signal.novelty_score:.2f}
            Credibility: {signal.credibility_score:.2f}
            Sentiment: {signal.sentiment_score:.2f}
            Liquidity: {signal.liquidity_score:.2f}
            
            Source: {signal.source}
            Time: {signal.created_at.isoformat()}
            """
            
            logger.info(
                f"Alert generated for {signal.ticker}",
                extra={
                    "signal_id": signal_id,
                    "ticker": signal.ticker,
                    "score": signal.total_score,
                    "alert_type": alert_type,
                }
            )
            
            # TODO: Implement actual alert sending (email, Slack, webhook)
            # For now, just log the alert
            
            return {
                "sent": True,
                "signal_id": signal_id,
                "ticker": signal.ticker,
                "score": signal.total_score,
                "alert_type": alert_type,
            }
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Alert sending failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)


def _format_digest(signals: List, digest_type: str) -> str:
    """
    Format signals into a digest email.

    Args:
        signals: List of Signal objects
        digest_type: Type of digest (Daily, Weekly)

    Returns:
        Formatted digest content
    """
    content = f"""
    📊 News Tunneler - {digest_type} Digest
    Generated: {datetime.now(timezone.utc).isoformat()}
    
    Top {len(signals)} Signals:
    """
    
    for i, signal in enumerate(signals, 1):
        content += f"""
        
        {i}. {signal.ticker} - Score: {signal.total_score:.2f}
           {signal.title}
           
           Catalyst: {signal.catalyst_score:.2f} | Novelty: {signal.novelty_score:.2f} | 
           Credibility: {signal.credibility_score:.2f} | Sentiment: {signal.sentiment_score:.2f} | 
           Liquidity: {signal.liquidity_score:.2f}
           
           Source: {signal.source}
           Time: {signal.created_at.isoformat()}
        """
    
    return content

