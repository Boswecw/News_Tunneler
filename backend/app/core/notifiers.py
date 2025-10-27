"""Notification handlers for alerts."""
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

# Debounce tracking: {url: last_notified_at}
_debounce_cache: dict[str, datetime] = {}
DEBOUNCE_WINDOW = timedelta(hours=1)


def should_notify(url: str) -> bool:
    """Check if we should notify for this URL (debounce)."""
    last_notified = _debounce_cache.get(url)
    if last_notified and datetime.utcnow() - last_notified < DEBOUNCE_WINDOW:
        return False
    
    _debounce_cache[url] = datetime.utcnow()
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
                            "text": f"Score: {score:.1f} | {datetime.utcnow().isoformat()}",
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
Time: {datetime.utcnow().isoformat()}
"""
        
        html = f"""
<html>
  <body>
    <h2>🚨 News Alert (Score: {score:.1f})</h2>
    <p><strong>{title}</strong></p>
    <p>{summary}</p>
    <p><a href="{url}">Read more</a></p>
    <p><small>{datetime.utcnow().isoformat()}</small></p>
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


async def notify_alert(title: str, summary: str, url: str, score: float) -> None:
    """Send alert via all enabled channels."""
    if not should_notify(url):
        logger.debug(f"Skipping debounced notification for: {url}")
        return
    
    await send_slack_alert(title, summary, url, score)
    send_email_alert(title, summary, url, score)

