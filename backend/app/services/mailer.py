"""
Email Service for Daily Opportunities Reports

Handles:
- Jinja2 template rendering (HTML + plain text)
- SMTP email sending with STARTTLS
- Optional PDF generation via WeasyPrint
- Idempotency via cache keys
"""
import smtplib
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.core.config import get_settings
from app.core.logging import logger
from app.services.report_builder import build_report_context


# Initialize Jinja2 environment
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(['html', 'xml']),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_report_email(context: Dict) -> Tuple[str, str]:
    """
    Render email templates (HTML and plain text).
    
    Args:
        context: Template context dict
    
    Returns:
        Tuple of (html_content, text_content)
    """
    try:
        html_template = jinja_env.get_template("email/top_opportunities.html.j2")
        text_template = jinja_env.get_template("email/top_opportunities.txt.j2")
        
        html_content = html_template.render(**context)
        text_content = text_template.render(**context)
        
        logger.info("Rendered email templates successfully")
        return html_content, text_content
    
    except Exception as e:
        logger.error(f"Failed to render email templates: {e}", exc_info=True)
        raise


def generate_pdf_report(html_content: str) -> Optional[bytes]:
    """
    Generate PDF from HTML content using WeasyPrint.
    
    Args:
        html_content: Rendered HTML string
    
    Returns:
        PDF bytes or None if disabled/failed
    """
    settings = get_settings()
    
    if not settings.enable_report_pdf:
        return None
    
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
        logger.info("Generated PDF report successfully")
        return pdf_bytes
    
    except ImportError:
        logger.warning("WeasyPrint not installed, skipping PDF generation")
        return None
    
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}", exc_info=True)
        return None


def send_email_smtp(
    subject: str,
    recipients: List[str],
    html_content: str,
    text_content: str,
    pdf_bytes: Optional[bytes] = None,
    pdf_filename: str = "opportunities_report.pdf"
) -> None:
    """
    Send email via SMTP with STARTTLS.
    
    Args:
        subject: Email subject
        recipients: List of recipient email addresses
        html_content: HTML email body
        text_content: Plain text email body
        pdf_bytes: Optional PDF attachment bytes
        pdf_filename: PDF attachment filename
    
    Raises:
        Exception if sending fails
    """
    settings = get_settings()
    
    if not settings.email_enabled:
        raise ValueError("Email not configured (missing SMTP settings)")
    
    # Create message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_user
    msg["To"] = ", ".join(recipients)
    
    # Attach text and HTML parts
    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))
    
    # Attach PDF if provided
    if pdf_bytes:
        pdf_part = MIMEApplication(pdf_bytes, _subtype="pdf")
        pdf_part.add_header("Content-Disposition", "attachment", filename=pdf_filename)
        msg.attach(pdf_part)
    
    # Send via SMTP
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {len(recipients)} recipients")
    
    except Exception as e:
        logger.error(f"Failed to send email: {e}", exc_info=True)
        raise


def generate_report_id(session_label: str, recipients: List[str]) -> str:
    """
    Generate unique report ID for logging and idempotency.
    
    Args:
        session_label: Trading session label
        recipients: List of recipient emails
    
    Returns:
        Report ID string (timestamp + hash)
    """
    et_tz = ZoneInfo("America/New_York")
    now_et = datetime.now(et_tz)
    date_str = now_et.strftime("%Y%m%d")

    # Extract first word from session label (e.g., "Pre-Market" -> "pre")
    session_part = session_label.lower().split("-")[0]

    recipients_hash = hashlib.md5(",".join(sorted(recipients)).encode()).hexdigest()[:8]

    return f"{date_str}_{session_part}_{recipients_hash}"


def check_idempotency(report_id: str) -> bool:
    """
    Check if report was already sent (12h window).
    
    Args:
        report_id: Report ID to check
    
    Returns:
        True if already sent, False otherwise
    
    Note: This is a placeholder. In production, use Redis or database cache.
    """
    # TODO: Implement with Redis or database cache
    # For now, always return False (allow sending)
    return False


def send_top_opportunities_report(
    recipients: List[str],
    session_label: str = "Pre-Market",
    force: bool = False
) -> Dict:
    """
    Build and send daily opportunities email report.
    
    Args:
        recipients: List of recipient email addresses
        session_label: Trading session (Pre-Market, Mid-Day, After-Close)
        force: Force send even if already sent today
    
    Returns:
        Dict with:
        - success: bool
        - report_id: str
        - candidates_count: int
        - recipients: list
        - error: str (if failed)
    """
    try:
        # Generate report ID
        report_id = generate_report_id(session_label, recipients)
        
        # Check idempotency
        if not force and check_idempotency(report_id):
            logger.info(f"Report {report_id} already sent, skipping")
            return {
                "success": True,
                "report_id": report_id,
                "candidates_count": 0,
                "recipients": recipients,
                "skipped": True,
            }
        
        # Build report context
        logger.info(f"Building report context for {session_label}...")
        context = build_report_context(session_label=session_label)
        
        candidates_count = context["total_candidates"]
        
        # Render templates
        html_content, text_content = render_report_email(context)
        
        # Generate PDF (optional)
        pdf_bytes = generate_pdf_report(html_content)
        
        # Build subject
        et_tz = ZoneInfo("America/New_York")
        now_et = datetime.now(et_tz)
        date_str = now_et.strftime("%B %d, %Y")
        subject = f"📊 Daily Opportunities Report - {session_label} - {date_str}"
        
        # Send email
        send_email_smtp(
            subject=subject,
            recipients=recipients,
            html_content=html_content,
            text_content=text_content,
            pdf_bytes=pdf_bytes,
            pdf_filename=f"opportunities_{report_id}.pdf"
        )
        
        logger.info(
            f"Report {report_id} sent successfully: "
            f"{candidates_count} candidates to {len(recipients)} recipients"
        )
        
        return {
            "success": True,
            "report_id": report_id,
            "candidates_count": candidates_count,
            "recipients": recipients,
        }
    
    except Exception as e:
        logger.error(f"Failed to send opportunities report: {e}", exc_info=True)
        return {
            "success": False,
            "report_id": report_id if 'report_id' in locals() else "unknown",
            "candidates_count": 0,
            "recipients": recipients,
            "error": str(e),
        }

