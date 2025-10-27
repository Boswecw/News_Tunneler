"""RSS/Atom feed fetching and parsing."""
import feedparser
import httpx
from datetime import datetime
from typing import TypedDict
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.logging import logger


class NormalizedArticle(TypedDict):
    """Normalized article structure."""
    url: str
    title: str
    summary: str
    source_name: str
    source_url: str
    source_type: str
    published_at: datetime
    ticker_guess: str | None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_feed(url: str) -> feedparser.FeedParserDict | None:
    """
    Fetch and parse RSS/Atom feed with retries.
    
    Returns parsed feed or None on failure.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            if feed.bozo:
                logger.warning(f"Feed parsing warning for {url}: {feed.bozo_exception}")
            
            return feed
    except Exception as e:
        logger.error(f"Failed to fetch feed {url}: {e}")
        raise


def normalize_article(
    entry: feedparser.FeedParserDict,
    source_name: str,
    source_url: str,
    source_type: str,
) -> NormalizedArticle | None:
    """
    Normalize a feed entry to standard article format.
    
    Returns NormalizedArticle or None if required fields missing.
    """
    try:
        # Extract URL
        url = entry.get("link") or entry.get("id")
        if not url:
            return None
        
        # Extract title
        title = entry.get("title", "").strip()
        if not title:
            return None
        
        # Extract summary
        summary = entry.get("summary", "") or entry.get("description", "")
        summary = summary.strip()
        
        # Extract published date
        published_at = None
        if entry.get("published_parsed"):
            published_at = datetime(*entry.published_parsed[:6])
        elif entry.get("updated_parsed"):
            published_at = datetime(*entry.updated_parsed[:6])
        else:
            published_at = datetime.utcnow()
        
        return NormalizedArticle(
            url=url,
            title=title,
            summary=summary,
            source_name=source_name,
            source_url=source_url,
            source_type=source_type,
            published_at=published_at,
            ticker_guess=None,  # Will be extracted later
        )
    except Exception as e:
        logger.error(f"Failed to normalize entry: {e}")
        return None

