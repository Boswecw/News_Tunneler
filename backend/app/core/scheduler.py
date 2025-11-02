"""Background scheduler for polling feeds."""
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Dict, Any
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
from app.core.predictive import train_symbol
from app.models import Source, Article, Score, Setting, PredictionBounds
from app.api.websocket import broadcast_alert

settings = get_settings()
scheduler = BackgroundScheduler()


async def trigger_price_model_training(ticker: str, plan: Dict[str, Any]) -> None:
    """
    Trigger price model training in background for a ticker with strong bullish signal.

    This runs asynchronously without blocking the article processing pipeline.

    Args:
        ticker: Stock ticker symbol
        plan: LLM analysis plan containing stance and confidence
    """
    try:
        stance = plan.get("stance", "NEUTRAL")
        confidence = plan.get("confidence_0to1", 0.0)

        # Only train on strong bullish signals
        if stance != "BULLISH" or confidence < 0.7:
            logger.debug(f"Skipping training for {ticker}: stance={stance}, confidence={confidence:.2f}")
            return

        logger.info(f"🚀 Auto-triggering price model training for {ticker} (stance={stance}, confidence={confidence:.2f})")

        # Import here to avoid circular dependency
        import httpx

        # Trigger training via internal API call (10y mode for robust predictions)
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"http://localhost:8000/api/training/train/{ticker}",
                params={
                    "mode": "10y",
                    "retain": "window",  # Keep 180 days for future reference
                    "window_days": 180,
                    "archive": True
                }
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"✅ Successfully trained {ticker}: R²={result['r2_score']:.4f}, "
                    f"observations={result['n_observations']}, "
                    f"model_path={result['model_path']}"
                )
            else:
                logger.error(f"❌ Training failed for {ticker}: {response.status_code} - {response.text}")

    except Exception as e:
        logger.error(f"Error triggering training for {ticker}: {e}", exc_info=True)


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

                        # Auto-trigger price model training for strong bullish signals
                        ticker = plan.get("ticker")
                        if ticker:
                            # Run training in background without blocking
                            asyncio.create_task(trigger_price_model_training(ticker, plan))

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


def refresh_opportunities_cache() -> None:
    """
    Refresh the opportunities cache by calling the opportunities endpoint.

    This runs periodically to ensure fresh opportunities are always available,
    even after backend restarts.
    """
    try:
        import httpx
        logger.info("🔄 Refreshing opportunities cache...")

        # Call the opportunities endpoint to trigger cache refresh
        response = httpx.get(
            "http://localhost:8000/api/signals/opportunities-tomorrow",
            params={"limit": 10},
            timeout=30.0
        )

        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Refreshed opportunities cache with {len(data)} opportunities")
        else:
            logger.error(f"❌ Failed to refresh opportunities cache: {response.status_code}")

    except Exception as e:
        logger.error(f"Error refreshing opportunities cache: {e}", exc_info=True)


def refresh_bounds_for_watchlist() -> None:
    """
    Refresh intraday bounds predictions for watchlist tickers.

    Runs during market hours (9:30 AM - 4:00 PM ET) every minute.
    Generates predictions and optionally stores them in database.
    """
    try:
        from zoneinfo import ZoneInfo
        from pathlib import Path
        import yfinance as yf
        import pandas as pd

        # Check if we're in market hours
        et_tz = ZoneInfo("America/New_York")
        now_et = datetime.now(et_tz)
        hour = now_et.hour
        minute = now_et.minute

        # Market hours: 9:30 AM - 4:00 PM ET
        if hour < 9 or (hour == 9 and minute < 30) or hour >= 16:
            # Outside market hours, skip
            return

        # Get config
        settings = get_settings()
        interval = settings.intraday_interval
        horizons = settings.intraday_horizons_list
        store_db = settings.predict_store_db

        # Get watchlist tickers (from recent signals or opportunities)
        with get_db_context() as db:
            from app.models import Signal
            from sqlalchemy import distinct

            # Get tickers with recent signals (last 24 hours)
            cutoff = datetime.utcnow() - timedelta(hours=24)
            cutoff_ms = int(cutoff.timestamp() * 1000)

            tickers = db.query(distinct(Signal.symbol)).filter(
                Signal.t >= cutoff_ms
            ).limit(20).all()  # Limit to 20 tickers to avoid overload

            tickers = [t[0] for t in tickers]

        if not tickers:
            logger.debug("No tickers in watchlist for bounds refresh")
            return

        logger.info(f"Refreshing bounds for {len(tickers)} tickers: {tickers}")

        # Import ML modules
        from app.ml.intraday_features import make_intraday_features
        from app.ml.intraday_models import load_model

        # Process each ticker
        for ticker in tickers:
            try:
                # Check if models exist
                model_dir = Path("backend/app/ml/artifacts")

                for H in horizons:
                    # Find model files
                    high_models = list(model_dir.glob(f"intraday_bounds_{ticker}_{interval}_high_{H}bars_*.joblib"))
                    low_models = list(model_dir.glob(f"intraday_bounds_{ticker}_{interval}_low_{H}bars_*.joblib"))

                    if not high_models or not low_models:
                        logger.debug(f"No models found for {ticker} horizon={H}, skipping")
                        continue

                    # Load most recent models
                    model_high_path = sorted(high_models)[-1]
                    model_low_path = sorted(low_models)[-1]

                    model_high, metadata_high = load_model(model_high_path)
                    model_low, metadata_low = load_model(model_low_path)

                    # Fetch recent data
                    stock = yf.Ticker(ticker)
                    df = stock.history(period='7d' if interval == '1m' else '60d', interval=interval)

                    if df.empty or len(df) < 50:
                        logger.warning(f"Insufficient data for {ticker}")
                        continue

                    # Create features
                    features = make_intraday_features(df, include_session_context=True)

                    # Predict
                    pred_high = model_high.predict(features)
                    pred_low = model_low.predict(features)

                    # Get quantiles
                    quantiles = sorted(pred_high.keys())
                    lower_q = quantiles[0]
                    upper_q = quantiles[-1]

                    # Get latest prediction
                    latest_idx = len(features) - 1
                    upper_bound = pred_high[upper_q][latest_idx]
                    lower_bound = pred_low[lower_q][latest_idx]
                    mid = (upper_bound + lower_bound) / 2

                    ts_ms = int(df.index[latest_idx].timestamp() * 1000)
                    model_version = metadata_high.get('trained_at', 'unknown')

                    # Store in database if enabled
                    if store_db:
                        with get_db_context() as db:
                            # Check if prediction already exists
                            existing = db.query(PredictionBounds).filter(
                                PredictionBounds.ticker == ticker,
                                PredictionBounds.ts == ts_ms,
                                PredictionBounds.interval == interval,
                                PredictionBounds.horizon == H
                            ).first()

                            if not existing:
                                prediction = PredictionBounds(
                                    ticker=ticker,
                                    ts=ts_ms,
                                    interval=interval,
                                    horizon=H,
                                    lower=round(lower_bound, 2),
                                    upper=round(upper_bound, 2),
                                    mid=round(mid, 2),
                                    model_version=model_version
                                )
                                db.add(prediction)
                                db.commit()
                                logger.debug(f"Stored bounds for {ticker} horizon={H}")

                    logger.debug(f"✅ Refreshed bounds for {ticker} horizon={H}: [{lower_bound:.2f}, {upper_bound:.2f}]")

            except Exception as e:
                logger.warning(f"Error refreshing bounds for {ticker}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error in bounds refresh job: {e}", exc_info=True)


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

    # Add predictive model training job - runs at 4:10 PM ET (after market close)
    scheduler.add_job(
        train_predictive_models,
        trigger=CronTrigger(hour=16, minute=10, day_of_week='mon-fri', timezone='America/New_York'),
        id="predictive_training",
        name="Train predictive models (4:10 PM ET, Mon-Fri)",
        replace_existing=True,
        misfire_grace_time=600,  # Allow up to 10 minutes delay
        coalesce=True,
        max_instances=1,
    )

    # Add research auto-labeling job - runs at 2 AM ET daily
    scheduler.add_job(
        run_research_autolabel,
        trigger=CronTrigger(hour=2, minute=0, timezone='America/New_York'),
        id="research_autolabel",
        name="Research auto-labeling (2 AM ET)",
        replace_existing=True,
        misfire_grace_time=600,  # Allow up to 10 minutes delay
        coalesce=True,
        max_instances=1,
    )

    # Add opportunities cache refresh job - runs every 15 minutes
    scheduler.add_job(
        refresh_opportunities_cache,
        trigger=IntervalTrigger(minutes=15),
        id="refresh_opportunities",
        name="Refresh opportunities cache (every 15 min)",
        replace_existing=True,
        misfire_grace_time=300,  # Allow up to 5 minutes delay
        coalesce=True,
        max_instances=1,
    )

    # Add daily opportunities report job - runs at 7:00 AM ET Mon-Fri
    scheduler.add_job(
        send_daily_opportunities_report,
        trigger=CronTrigger(
            day_of_week='mon-fri',
            hour=7,
            minute=0,
            timezone='America/New_York'
        ),
        id="daily_opportunities_report",
        name="Send daily opportunities report (7:00 AM ET Mon-Fri)",
        replace_existing=True,
        misfire_grace_time=300,  # Allow up to 5 minutes delay
        coalesce=True,
        max_instances=1,
    )

    # Add intraday bounds refresh job - runs every minute during market hours
    scheduler.add_job(
        refresh_bounds_for_watchlist,
        trigger=IntervalTrigger(minutes=1),
        id="refresh_intraday_bounds",
        name="Refresh intraday bounds predictions (every 1 min during market hours)",
        replace_existing=True,
        misfire_grace_time=60,  # Allow up to 1 minute delay
        coalesce=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info("Scheduler started with RSS polling, morning digest (11 AM ET), evening digest (5 PM ET), cleanup (1 AM ET), bulk LLM analysis (4x daily), predictive training (4:10 PM ET Mon-Fri), research auto-labeling (2 AM ET), opportunities refresh (every 15 min), daily opportunities report (7:00 AM ET Mon-Fri), and intraday bounds refresh (every 1 min during market hours)")

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


def train_predictive_models() -> None:
    """Train predictive models for all active symbols after market close."""
    try:
        logger.info("Starting predictive model training...")

        # Get list of symbols from intraday cache
        from app.api.stream import _intraday_cache

        symbols = list(_intraday_cache.keys())

        if not symbols:
            logger.info("No symbols in cache, skipping predictive training")
            return

        success_count = 0
        fail_count = 0

        for symbol in symbols:
            try:
                cache_entry = _intraday_cache.get(symbol)
                if cache_entry and cache_entry.get("data"):
                    logger.info(f"Training predictive model for {symbol}...")
                    success = train_symbol(symbol, cache_entry["data"])
                    if success:
                        success_count += 1
                        logger.info(f"Successfully trained model for {symbol}")
                    else:
                        fail_count += 1
                        logger.warning(f"Failed to train model for {symbol}")
                else:
                    logger.warning(f"No data available for {symbol}")
                    fail_count += 1
            except Exception as e:
                logger.error(f"Error training model for {symbol}: {e}")
                fail_count += 1

        logger.info(f"Predictive training complete: {success_count} successful, {fail_count} failed")

    except Exception as e:
        logger.error(f"Error in predictive model training: {e}", exc_info=True)


def run_research_autolabel() -> None:
    """Run research auto-labeling job to generate training labels from realized returns."""
    try:
        logger.info("Starting research auto-labeling job...")
        from app.jobs.research_autolabel import run
        run(limit=250)
        logger.info("Research auto-labeling job complete")
    except Exception as e:
        logger.error(f"Error in research auto-labeling job: {e}", exc_info=True)


def send_daily_opportunities_report() -> None:
    """
    Send daily opportunities email report at 7:00 AM ET (Mon-Fri).

    Determines session label based on current time:
    - Before 9 AM: Pre-Market
    - 9 AM - 4 PM: Mid-Day
    - After 4 PM: After-Close
    """
    try:
        from zoneinfo import ZoneInfo
        from app.services.mailer import send_top_opportunities_report

        settings = get_settings()
        recipients = settings.report_recipients

        if not recipients:
            logger.warning("No report recipients configured; skipping daily report")
            return

        # Determine session label based on current ET time
        et_tz = ZoneInfo("America/New_York")
        now_et = datetime.now(et_tz)
        hour = now_et.hour

        if hour < 9:
            session_label = "Pre-Market"
        elif hour < 16:
            session_label = "Mid-Day"
        else:
            session_label = "After-Close"

        logger.info(f"Sending daily opportunities report ({session_label}) to {len(recipients)} recipients...")

        result = send_top_opportunities_report(recipients, session_label=session_label)

        if result.get("success"):
            logger.info(
                f"✅ Daily report sent successfully: {result['report_id']} "
                f"({result['candidates_count']} candidates)"
            )
        else:
            logger.error(f"❌ Daily report failed: {result.get('error')}")

    except Exception as e:
        logger.error(f"Error sending daily opportunities report: {e}", exc_info=True)


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

