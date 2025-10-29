"""Background scheduler for polling feeds."""
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from sqlalchemy import and_
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
from app.core.notifiers import notify_alert, send_morning_digest_job, send_evening_digest_job
from app.core.llm import analyze_article
from app.core.strategies import map_to_strategy
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

                        # Send Slack notifications only (email is sent in daily digest)
                        from app.core.notifiers import send_slack_alert
                        await send_slack_alert(
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


def process_high_score_articles(limit: int = 10) -> None:
    """
    Process high-scoring articles that don't have LLM analysis yet.

    This job runs after RSS polling to analyze articles that meet the
    LLM_MIN_ALERT_SCORE threshold.

    Args:
        limit: Maximum number of articles to process per run (default: 10)
    """
    if not settings.llm_enabled:
        logger.debug("LLM not enabled, skipping auto-analysis")
        return

    try:
        logger.info("Starting LLM auto-processing job...")

        with get_db_context() as db:
            # Get current min_alert_score from settings
            setting = db.query(Setting).filter(Setting.id == 1).first()
            min_score = setting.min_alert_score if setting else settings.llm_min_alert_score

            # Find articles without LLM analysis that have high scores
            articles_to_analyze = (
                db.query(Article, Score)
                .join(Score, Article.id == Score.article_id)
                .filter(
                    and_(
                        Article.llm_plan.is_(None),  # No LLM analysis yet
                        Score.total >= min_score,  # High score
                    )
                )
                .order_by(Score.total.desc())
                .limit(limit)  # Process max N articles per run to avoid rate limits
                .all()
            )

            if not articles_to_analyze:
                logger.info("No high-scoring articles need LLM analysis")
                return

            logger.info(f"Found {len(articles_to_analyze)} articles to analyze")

            for article, score in articles_to_analyze:
                try:
                    # Build payload for LLM
                    payload = {
                        "title": article.title,
                        "summary": article.summary or "",
                        "url": article.url,
                        "source_name": article.source_name,
                        "source_url": article.source_url,
                        "published_at": article.published_at.isoformat() if article.published_at else "",
                        "rule_catalyst": score.catalyst,
                        "rule_novelty": score.novelty,
                        "rule_credibility": score.credibility,
                    }

                    # Run LLM analysis
                    logger.info(f"Analyzing article {article.id}: {article.title[:50]}...")
                    plan = analyze_article(payload)

                    # Map to strategy
                    strategy = map_to_strategy(plan)

                    # Update article with results
                    article.llm_plan = plan
                    article.strategy_bucket = strategy["bucket"]
                    article.strategy_risk = strategy["risk"]

                    # Update ticker_guess from LLM analysis if available
                    if plan.get("ticker"):
                        article.ticker_guess = plan["ticker"]

                    db.add(article)
                    db.commit()

                    logger.info(f"✅ Article {article.id} analyzed: {strategy['bucket']}")

                    # Generate trading signals
                    try:
                        from app.api.signals import ingest_article as generate_signals
                        signal_payload = {
                            "article_id": article.id,
                            "title": article.title,
                            "summary": article.summary or "",
                            "full_text": "",
                            "source_name": article.source_name,
                            "llm_plan": plan,
                        }
                        result = generate_signals(signal_payload)
                        logger.info(f"Generated {result['count']} signals for article {article.id}")
                    except Exception as sig_err:
                        logger.error(f"Error generating signals for article {article.id}: {sig_err}")

                except Exception as e:
                    logger.error(f"Error analyzing article {article.id}: {e}")
                    db.rollback()
                    continue

            logger.info(f"LLM auto-processing complete. Analyzed {len(articles_to_analyze)} articles")

    except Exception as e:
        logger.error(f"Error in LLM auto-processing job: {e}", exc_info=True)


def analyze_all_high_score_articles() -> None:
    """
    Scheduled job to analyze ALL high-scoring articles without LLM analysis.

    Runs 4 times a day (6 AM, 12 PM, 6 PM, 12 AM ET) to ensure all articles
    get analyzed even if they were missed during RSS polling.

    Processes up to 50 articles per run to handle backlog.
    """
    logger.info("🔍 Starting scheduled bulk LLM analysis job...")
    process_high_score_articles(limit=50)


def _run_poll_feeds_sync():
    """Synchronous wrapper for async poll_feeds function."""
    logger.info("Scheduler job triggered - starting poll...")
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Run the async function
            loop.run_until_complete(poll_feeds())
            logger.info("Scheduled poll completed successfully")

            # After polling, process high-scoring articles with LLM
            process_high_score_articles()

        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Error in scheduled poll: {e}", exc_info=True)


def start_scheduler() -> None:
    """Start the background scheduler."""
    if scheduler.running:
        logger.warning("Scheduler already running")
        return

    poll_interval = settings.poll_interval_sec
    logger.info(f"Starting scheduler with {poll_interval}s interval")

    # Add RSS polling job
    scheduler.add_job(
        _run_poll_feeds_sync,
        trigger=IntervalTrigger(seconds=poll_interval),
        id="poll_feeds",
        name="Poll RSS feeds",
        replace_existing=True,
        misfire_grace_time=30,  # Allow up to 30 seconds delay
        coalesce=True,  # Combine multiple missed executions into one
        max_instances=1,  # Only one instance at a time
    )

    # Add morning digest job - runs at 11 AM ET
    # Using America/New_York timezone to handle DST automatically
    scheduler.add_job(
        send_morning_digest_job,
        trigger=CronTrigger(hour=11, minute=0, timezone='America/New_York'),
        id="morning_digest",
        name="Send morning digest email (11 AM ET)",
        replace_existing=True,
        misfire_grace_time=300,  # Allow up to 5 minutes delay
        coalesce=True,
        max_instances=1,
    )

    # Add evening digest job - runs at 5 PM ET
    scheduler.add_job(
        send_evening_digest_job,
        trigger=CronTrigger(hour=17, minute=0, timezone='America/New_York'),
        id="evening_digest",
        name="Send evening digest email (5 PM ET)",
        replace_existing=True,
        misfire_grace_time=300,  # Allow up to 5 minutes delay
        coalesce=True,
        max_instances=1,
    )

    # Add cleanup job - runs at 1 AM ET daily
    scheduler.add_job(
        cleanup_old_articles,
        trigger=CronTrigger(hour=1, minute=0, timezone='America/New_York'),
        id="cleanup_old_articles",
        name="Cleanup old articles (1 AM ET)",
        replace_existing=True,
        misfire_grace_time=300,  # Allow up to 5 minutes delay
        coalesce=True,
        max_instances=1,
    )

    # Add bulk LLM analysis jobs - runs 4 times a day (6 AM, 12 PM, 6 PM, 12 AM ET)
    scheduler.add_job(
        analyze_all_high_score_articles,
        trigger=CronTrigger(hour=0, minute=0, timezone='America/New_York'),
        id="llm_analysis_midnight",
        name="Bulk LLM analysis (12 AM ET)",
        replace_existing=True,
        misfire_grace_time=600,  # Allow up to 10 minutes delay
        coalesce=True,
        max_instances=1,
    )

    scheduler.add_job(
        analyze_all_high_score_articles,
        trigger=CronTrigger(hour=6, minute=0, timezone='America/New_York'),
        id="llm_analysis_morning",
        name="Bulk LLM analysis (6 AM ET)",
        replace_existing=True,
        misfire_grace_time=600,  # Allow up to 10 minutes delay
        coalesce=True,
        max_instances=1,
    )

    scheduler.add_job(
        analyze_all_high_score_articles,
        trigger=CronTrigger(hour=12, minute=0, timezone='America/New_York'),
        id="llm_analysis_noon",
        name="Bulk LLM analysis (12 PM ET)",
        replace_existing=True,
        misfire_grace_time=600,  # Allow up to 10 minutes delay
        coalesce=True,
        max_instances=1,
    )

    scheduler.add_job(
        analyze_all_high_score_articles,
        trigger=CronTrigger(hour=18, minute=0, timezone='America/New_York'),
        id="llm_analysis_evening",
        name="Bulk LLM analysis (6 PM ET)",
        replace_existing=True,
        misfire_grace_time=600,  # Allow up to 10 minutes delay
        coalesce=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info("Scheduler started with RSS polling, morning digest (11 AM ET), evening digest (5 PM ET), cleanup (1 AM ET), and bulk LLM analysis (4x daily)")

    # Run first poll immediately in background
    import threading
    threading.Thread(target=_run_poll_feeds_sync, daemon=True).start()


def cleanup_old_articles() -> None:
    """Delete articles older than 2 days (48 hours)."""
    try:
        logger.info("Starting cleanup of old articles...")

        with get_db_context() as db:
            # Calculate cutoff time (2 days ago)
            cutoff_time = datetime.utcnow() - timedelta(days=2)

            # Find articles older than 2 days
            old_articles = db.query(Article).filter(
                Article.published_at < cutoff_time
            ).all()

            count = len(old_articles)

            if count == 0:
                logger.info("No old articles to delete")
                return

            # Delete associated scores first, then articles
            article_ids = [article.id for article in old_articles]

            # Delete scores
            db.query(Score).filter(Score.article_id.in_(article_ids)).delete(synchronize_session=False)

            # Delete articles
            db.query(Article).filter(Article.id.in_(article_ids)).delete(synchronize_session=False)

            db.commit()
            logger.info(f"Deleted {count} articles older than 2 days (published before {cutoff_time})")

    except Exception as e:
        logger.error(f"Error cleaning up old articles: {e}", exc_info=True)


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

