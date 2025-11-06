"""Notification handlers for alerts."""
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

# Debounce tracking: {url: last_notified_at}
_debounce_cache: dict[str, datetime] = {}
DEBOUNCE_WINDOW = timedelta(hours=1)


def should_notify(url: str) -> bool:
    """Check if we should notify for this URL (debounce)."""
    last_notified = _debounce_cache.get(url)
    if last_notified and datetime.now(timezone.utc) - last_notified < DEBOUNCE_WINDOW:
        return False

    _debounce_cache[url] = datetime.now(timezone.utc)
    return True


async def send_slack_alert(title: str, summary: str, url: str, score: float) -> bool:
    """Send alert to Slack webhook."""
    if not settings.slack_enabled:
        return False
    
    try:
        message = {
            "text": f"🚨 News Alert (Score: {score:.1f})",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{title}*\n{summary[:200]}...\n<{url}|Read more>",
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Score: {score:.1f} | {datetime.now(timezone.utc).isoformat()}",
                        }
                    ],
                },
            ],
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(settings.slack_webhook_url, json=message)
            response.raise_for_status()
            logger.info(f"Slack alert sent for: {title[:50]}")
            return True
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")
        return False


def send_email_alert(title: str, summary: str, url: str, score: float) -> bool:
    """Send alert via email."""
    if not settings.email_enabled:
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"News Alert: {title[:60]}"
        msg["From"] = settings.smtp_user
        msg["To"] = settings.alert_email_to

        text = f"""
News Alert (Score: {score:.1f})

Title: {title}
Summary: {summary}
URL: {url}
Time: {datetime.now(timezone.utc).isoformat()}
"""

        html = f"""
<html>
  <body>
    <h2>🚨 News Alert (Score: {score:.1f})</h2>
    <p><strong>{title}</strong></p>
    <p>{summary}</p>
    <p><a href="{url}">Read more</a></p>
    <p><small>{datetime.now(timezone.utc).isoformat()}</small></p>
  </body>
</html>
"""

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

        logger.info(f"Email alert sent for: {title[:50]}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        return False


def send_daily_digest(articles: list[dict], digest_type: str = "Daily") -> bool:
    """
    Send digest email with high-scoring BULLISH articles.

    Args:
        articles: List of article dictionaries with title, score, ticker, sector, simple_explanation, etc.
        digest_type: Type of digest ("Morning" or "Evening") for email subject/header

    Returns:
        True if email sent successfully, False otherwise
    """
    if not settings.email_enabled:
        return False

    if not articles:
        logger.info(f"No articles for {digest_type.lower()} digest - skipping email")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"News Tunneler {digest_type} Digest - {len(articles)} Bullish Opportunities"
        msg["From"] = settings.smtp_user
        msg["To"] = settings.alert_email_to

        # Build text version
        text_parts = [
            f"News Tunneler {digest_type} Digest",
            f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
            f"Total Bullish Articles: {len(articles)}",
            f"",
            "=" * 80,
            ""
        ]

        for i, article in enumerate(articles, 1):
            text_parts.extend([
                f"{i}. {article['title']} (Score: {article['score']:.1f})",
                f"   Ticker: {article.get('ticker', 'N/A')} | Sector: {article.get('sector', 'N/A')}",
                f"   Source: {article['source_name']}",
                f"   Published: {article['published_at']}",
                f"   {article.get('simple_explanation', article['summary'])[:300]}...",
                f"   URL: {article['url']}",
                ""
            ])

        text = "\n".join(text_parts)

        # Build HTML version
        html_parts = [
            "<html>",
            "<head>",
            "<style>",
            "  body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }",
            "  .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }",
            "  .article { border-left: 4px solid #10b981; padding: 15px; margin: 20px 0; background: #f9f9f9; border-radius: 4px; }",
            "  .score { display: inline-block; background: #667eea; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; }",
            "  .bullish-badge { display: inline-block; background: #10b981; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; margin-left: 8px; }",
            "  .meta { color: #666; font-size: 0.9em; margin: 8px 0; }",
            "  .explanation { margin: 10px 0; padding: 12px; background: #e8f5e9; border-left: 3px solid #10b981; border-radius: 4px; }",
            "  .read-more { display: inline-block; background: #667eea; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-top: 10px; }",
            "  .read-more:hover { background: #764ba2; }",
            "</style>",
            "</head>",
            "<body>",
            "<div class='header'>",
            f"  <h1>📰 News Tunneler {digest_type} Digest</h1>",
            f"  <p>Date: {datetime.now(timezone.utc).strftime('%B %d, %Y')}</p>",
            f"  <p>Total Bullish Opportunities: {len(articles)}</p>",
            "</div>",
        ]

        for i, article in enumerate(articles, 1):
            html_parts.extend([
                "<div class='article'>",
                f"  <h3>{i}. {article['title']}</h3>",
                f"  <span class='score'>Score: {article['score']:.1f}</span>",
                f"  <span class='bullish-badge'>🚀 BULLISH</span>",
                f"  <div class='meta'>",
                f"    <strong>Ticker:</strong> {article.get('ticker', 'N/A')} | ",
                f"    <strong>Sector:</strong> {article.get('sector', 'N/A')} | ",
                f"    <strong>Source:</strong> {article['source_name']} | ",
                f"    <strong>Published:</strong> {article['published_at']}",
                f"  </div>",
            ])

            # Use simple_explanation if available, otherwise fall back to summary
            explanation = article.get('simple_explanation', article.get('summary', ''))
            if explanation:
                html_parts.append(f"  <div class='explanation'><strong>What This Means:</strong> {explanation}</div>")

            html_parts.extend([
                f"  <a href='{article['url']}' class='read-more'>Read Full Article →</a>",
                "</div>",
            ])

        html_parts.extend([
            "<div style='margin-top: 30px; padding: 20px; background: #f0f0f0; border-radius: 4px; text-align: center;'>",
            f"  <p style='color: #666; margin: 0;'>This is your {digest_type.lower()} digest from News Tunneler</p>",
            f"  <p style='color: #999; font-size: 0.9em; margin: 5px 0 0 0;'>Generated at {datetime.now(timezone.utc).strftime('%I:%M %p UTC')}</p>",
            "</div>",
            "</body>",
            "</html>",
        ])

        html = "\n".join(html_parts)

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

        logger.info(f"{digest_type} digest email sent with {len(articles)} articles")
        return True
    except Exception as e:
        logger.error(f"Failed to send {digest_type.lower()} digest email: {e}")
        return False


async def notify_alert(title: str, summary: str, url: str, score: float) -> None:
    """Send alert via all enabled channels."""
    if not should_notify(url):
        logger.debug(f"Skipping debounced notification for: {url}")
        return

    await send_slack_alert(title, summary, url, score)
    send_email_alert(title, summary, url, score)


def send_morning_digest_job() -> None:
    """
    Send morning digest email with BULLISH articles from the past 12 hours (11 PM - 11 AM ET).

    This job runs at 11:00 AM Eastern Time and includes articles published since 11 PM the previous day.
    Only includes articles with:
    - Score >= LLM_MIN_ALERT_SCORE
    - LLM analysis completed (llm_plan is not null)
    - Stance is BULLISH
    """
    from datetime import datetime, timedelta
    from app.core.db import get_db_context
    from app.models import Article, Score, Setting
    from sqlalchemy import and_
    import json

    logger.info("Starting morning digest job...")

    try:
        with get_db_context() as db:
            # Get current settings for min_alert_score
            setting = db.query(Setting).filter(Setting.id == 1).first()
            min_alert_score = setting.min_alert_score if setting else settings.llm_min_alert_score

            # Get articles from the past 12 hours with score >= min_alert_score
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=12)

            results = (
                db.query(Article, Score)
                .join(Score, Article.id == Score.article_id)
                .filter(
                    and_(
                        Article.published_at >= cutoff_time,
                        Score.total >= min_alert_score,
                        Article.llm_plan.isnot(None)  # Must have LLM analysis
                    )
                )
                .order_by(Score.total.desc())
                .all()
            )

            if not results:
                logger.info("No BULLISH articles in the past 12 hours for morning digest")
                return

            # Filter for BULLISH stance and format articles for email
            articles = []
            for article, score in results:
                try:
                    # Parse llm_plan JSON
                    llm_plan = article.llm_plan if isinstance(article.llm_plan, dict) else json.loads(article.llm_plan)

                    # Only include BULLISH articles
                    if llm_plan.get('stance') != 'BULLISH':
                        continue

                    articles.append({
                        "title": article.title,
                        "summary": article.summary or "",
                        "url": article.url,
                        "score": score.total,
                        "source_name": article.source_name,
                        "published_at": article.published_at.strftime("%Y-%m-%d %H:%M UTC"),
                        "ticker": llm_plan.get('ticker', 'N/A'),
                        "sector": llm_plan.get('sector', 'N/A'),
                        "simple_explanation": llm_plan.get('simple_explanation', ''),
                    })
                except Exception as e:
                    logger.error(f"Error processing article {article.id} for morning digest: {e}")
                    continue

            if not articles:
                logger.info("No BULLISH articles found after filtering for morning digest")
                return

            # Send the morning digest email
            send_daily_digest(articles, digest_type="Morning")
            logger.info(f"Morning digest job complete. Sent {len(articles)} BULLISH articles")

    except Exception as e:
        logger.error(f"Error in morning digest job: {e}", exc_info=True)


def send_evening_digest_job() -> None:
    """
    Send evening digest email with BULLISH articles from the past 12 hours (11 AM - 5 PM ET).

    This job runs at 5:00 PM Eastern Time and includes articles published since 11 AM the same day.
    Only includes articles with:
    - Score >= LLM_MIN_ALERT_SCORE
    - LLM analysis completed (llm_plan is not null)
    - Stance is BULLISH
    """
    from datetime import datetime, timedelta
    from app.core.db import get_db_context
    from app.models import Article, Score, Setting
    from sqlalchemy import and_
    import json

    logger.info("Starting evening digest job...")

    try:
        with get_db_context() as db:
            # Get current settings for min_alert_score
            setting = db.query(Setting).filter(Setting.id == 1).first()
            min_alert_score = setting.min_alert_score if setting else settings.llm_min_alert_score

            # Get articles from the past 6 hours (11 AM - 5 PM is 6 hours)
            # Using 6 hours to avoid overlap with morning digest
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=6)

            results = (
                db.query(Article, Score)
                .join(Score, Article.id == Score.article_id)
                .filter(
                    and_(
                        Article.published_at >= cutoff_time,
                        Score.total >= min_alert_score,
                        Article.llm_plan.isnot(None)  # Must have LLM analysis
                    )
                )
                .order_by(Score.total.desc())
                .all()
            )

            if not results:
                logger.info("No BULLISH articles in the past 6 hours for evening digest")
                return

            # Filter for BULLISH stance and format articles for email
            articles = []
            for article, score in results:
                try:
                    # Parse llm_plan JSON
                    llm_plan = article.llm_plan if isinstance(article.llm_plan, dict) else json.loads(article.llm_plan)

                    # Only include BULLISH articles
                    if llm_plan.get('stance') != 'BULLISH':
                        continue

                    articles.append({
                        "title": article.title,
                        "summary": article.summary or "",
                        "url": article.url,
                        "score": score.total,
                        "source_name": article.source_name,
                        "published_at": article.published_at.strftime("%Y-%m-%d %H:%M UTC"),
                        "ticker": llm_plan.get('ticker', 'N/A'),
                        "sector": llm_plan.get('sector', 'N/A'),
                        "simple_explanation": llm_plan.get('simple_explanation', ''),
                    })
                except Exception as e:
                    logger.error(f"Error processing article {article.id} for evening digest: {e}")
                    continue

            if not articles:
                logger.info("No BULLISH articles found after filtering for evening digest")
                return

            # Send the evening digest email
            send_daily_digest(articles, digest_type="Evening")
            logger.info(f"Evening digest job complete. Sent {len(articles)} BULLISH articles")

    except Exception as e:
        logger.error(f"Error in evening digest job: {e}", exc_info=True)

