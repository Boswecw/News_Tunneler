"""Background scheduler for polling feeds."""
import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.core.db import get_db_context
from app.core.config import get_settings
from app.core.logging import logger
from app.core.rss import fetch_feed, normalize_article
from app.core.dedupe import article_exists
from app.core.scoring import (
    score_catalyst,
    score_novelty,
    score_credibility,
    score_liquidity,
    compute_total_score,
)
from app.core.sentiment import analyze_sentiment
from app.core.tickers import extract_ticker
from app.core.notifiers import notify_alert
from app.models import Source, Article, Score, Setting
from app.api.websocket import broadcast_alert

settings = get_settings()
scheduler = BackgroundScheduler()


async def poll_feeds() -> None:
    """Poll all enabled feeds and process articles."""
    logger.info("Starting feed poll...")
    
    with get_db_context() as db:
        sources = db.query(Source).filter(Source.enabled == True).all()
        
        if not sources:
            logger.warning("No enabled sources found")
            return
        
        # Get current settings for scoring weights
        setting = db.query(Setting).filter(Setting.id == 1).first()
        weights = {
            "catalyst": setting.weight_catalyst if setting else 1.0,
            "novelty": setting.weight_novelty if setting else 1.0,
            "credibility": setting.weight_credibility if setting else 1.0,
            "sentiment": setting.weight_sentiment if setting else 1.0,
            "liquidity": setting.weight_liquidity if setting else 1.0,
        }
        min_alert_score = setting.min_alert_score if setting else 12.0
        
        new_articles_count = 0
        
        for source in sources:
            try:
                feed = await fetch_feed(source.url)
                if not feed or not feed.entries:
                    logger.warning(f"No entries in feed: {source.name}")
                    continue
                
                for entry in feed.entries[:20]:  # Limit to 20 entries per feed
                    normalized = normalize_article(
                        entry,
                        source.name,
                        source.url,
                        source.source_type,
                    )
                    
                    if not normalized:
                        continue
                    
                    # Check for duplicates
                    if article_exists(db, normalized["url"], normalized["title"]):
                        logger.debug(f"Article already exists: {normalized['title'][:50]}")
                        continue
                    
                    # Extract ticker
                    ticker = extract_ticker(f"{normalized['title']} {normalized['summary']}")
                    
                    # Create article
                    article = Article(
                        url=normalized["url"],
                        title=normalized["title"],
                        summary=normalized["summary"],
                        source_name=normalized["source_name"],
                        source_url=normalized["source_url"],
                        source_type=normalized["source_type"],
                        published_at=normalized["published_at"],
                        ticker_guess=ticker,
                    )
                    db.add(article)
                    db.flush()  # Get the article ID
                    
                    # Compute scores
                    catalyst = score_catalyst(article.title, article.summary)
                    novelty = score_novelty(article.published_at)
                    credibility = score_credibility(article.source_url)
                    sentiment = analyze_sentiment(f"{article.title} {article.summary}")
                    liquidity = score_liquidity(ticker)
                    
                    total = compute_total_score(
                        catalyst, novelty, credibility, sentiment, liquidity, weights
                    )
                    
                    # Create score
                    score = Score(
                        article_id=article.id,
                        catalyst=catalyst,
                        novelty=novelty,
                        credibility=credibility,
                        sentiment=sentiment,
                        liquidity=liquidity,
                        total=total,
                    )
                    db.add(score)
                    db.flush()
                    
                    logger.info(
                        f"New article: {article.title[:50]}... (score: {total:.1f})"
                    )
                    new_articles_count += 1
                    
                    # Broadcast if above threshold
                    if total >= min_alert_score:
                        await broadcast_alert({
                            "id": article.id,
                            "title": article.title,
                            "summary": article.summary[:200],
                            "url": article.url,
                            "score": total,
                            "ticker": ticker,
                            "source": article.source_name,
                        })
                        
                        # Send notifications
                        await notify_alert(
                            article.title,
                            article.summary,
                            article.url,
                            total,
                        )
                
                # Update last_fetched_at
                source.last_fetched_at = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Error polling source {source.name}: {e}")
        
        db.commit()
        logger.info(f"Feed poll complete. New articles: {new_articles_count}")


def start_scheduler() -> None:
    """Start the background scheduler."""
    if scheduler.running:
        logger.warning("Scheduler already running")
        return
    
    poll_interval = settings.poll_interval_sec
    logger.info(f"Starting scheduler with {poll_interval}s interval")
    
    scheduler.add_job(
        lambda: asyncio.run(poll_feeds()),
        trigger=IntervalTrigger(seconds=poll_interval),
        id="poll_feeds",
        name="Poll RSS feeds",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

