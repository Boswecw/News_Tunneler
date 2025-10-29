"""
RSS Polling Tasks

Celery tasks for asynchronous RSS feed polling and processing.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.core.celery_app import celery_app
from app.core.structured_logging import get_logger
from app.core.feature_flags import is_feature_enabled, FeatureFlag

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.rss_tasks.poll_rss_feed",
    max_retries=3,
    default_retry_delay=300,  # Retry after 5 minutes
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def poll_rss_feed(self, source_id: int) -> Dict[str, Any]:
    """
    Poll a single RSS feed for new articles.
    
    Args:
        source_id: ID of the RSS source to poll
        
    Returns:
        Summary of polling results
    """
    if not is_feature_enabled(FeatureFlag.RSS_POLLING):
        logger.warning("RSS polling is disabled via feature flag")
        return {
            "source_id": source_id,
            "new_articles": 0,
            "error": "RSS polling disabled"
        }
    
    try:
        from app.core.db import SessionLocal
        from app.models.source import Source
        from app.core.rss import fetch_rss_feed
        
        logger.info(f"Polling RSS feed: source_id={source_id}")
        
        db = SessionLocal()
        try:
            # Get source
            source = db.query(Source).filter(Source.id == source_id).first()
            if not source:
                logger.warning(f"Source not found: {source_id}")
                return {
                    "source_id": source_id,
                    "new_articles": 0,
                    "error": "Source not found"
                }
            
            # Fetch RSS feed
            articles = fetch_rss_feed(source.url)
            
            logger.info(
                f"Fetched {len(articles)} articles from {source.name}",
                extra={
                    "source_id": source_id,
                    "source_name": source.name,
                    "article_count": len(articles),
                }
            )
            
            # Queue LLM analysis for new articles
            from app.tasks.llm_tasks import analyze_article_async
            
            queued = 0
            for article in articles:
                try:
                    analyze_article_async.delay(article)
                    queued += 1
                except Exception as e:
                    logger.error(f"Failed to queue article analysis: {e}")
            
            return {
                "source_id": source_id,
                "source_name": source.name,
                "new_articles": len(articles),
                "queued_for_analysis": queued,
            }
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(
            f"RSS polling failed: {str(e)}",
            exc_info=True,
            extra={
                "source_id": source_id,
                "error": str(e),
            }
        )
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    name="app.tasks.rss_tasks.poll_all_rss_feeds",
    max_retries=2,
)
def poll_all_rss_feeds(self) -> Dict[str, Any]:
    """
    Poll all active RSS feeds.
    
    Returns:
        Summary of polling results for all feeds
    """
    if not is_feature_enabled(FeatureFlag.RSS_POLLING):
        logger.warning("RSS polling is disabled via feature flag")
        return {
            "total_sources": 0,
            "polled": 0,
            "error": "RSS polling disabled"
        }
    
    try:
        from app.core.db import SessionLocal
        from app.models.source import Source
        
        logger.info("Polling all RSS feeds")
        
        db = SessionLocal()
        try:
            # Get all active sources
            sources = db.query(Source).filter(Source.active == True).all()
            
            logger.info(f"Found {len(sources)} active RSS sources")
            
            # Queue polling tasks for each source
            tasks = []
            for source in sources:
                try:
                    task = poll_rss_feed.delay(source.id)
                    tasks.append({
                        "source_id": source.id,
                        "source_name": source.name,
                        "task_id": task.id,
                    })
                except Exception as e:
                    logger.error(f"Failed to queue source {source.id}: {e}")
            
            logger.info(
                f"Queued {len(tasks)} RSS polling tasks",
                extra={
                    "total_sources": len(sources),
                    "queued": len(tasks),
                }
            )
            
            return {
                "total_sources": len(sources),
                "queued": len(tasks),
                "tasks": tasks,
            }
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Polling all feeds failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    name="app.tasks.rss_tasks.cleanup_old_signals",
    max_retries=1,
)
def cleanup_old_signals(self, days_old: int = 30) -> Dict[str, Any]:
    """
    Clean up old signals from the database.
    
    Args:
        days_old: Delete signals older than this many days
        
    Returns:
        Summary of cleanup results
    """
    try:
        from app.core.db import SessionLocal
        from app.models.signal import Signal
        
        logger.info(f"Cleaning up signals older than {days_old} days")
        
        db = SessionLocal()
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Delete old signals
            deleted = db.query(Signal).filter(
                Signal.created_at < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(
                f"Deleted {deleted} old signals",
                extra={
                    "deleted_count": deleted,
                    "cutoff_date": cutoff_date.isoformat(),
                }
            )
            
            return {
                "deleted_count": deleted,
                "cutoff_date": cutoff_date.isoformat(),
            }
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    name="app.tasks.rss_tasks.refresh_source_metadata",
    max_retries=2,
)
def refresh_source_metadata(self, source_id: int) -> Dict[str, Any]:
    """
    Refresh metadata for an RSS source (title, description, etc.).
    
    Args:
        source_id: ID of the RSS source
        
    Returns:
        Updated source metadata
    """
    try:
        from app.core.db import SessionLocal
        from app.models.source import Source
        import feedparser
        
        logger.info(f"Refreshing metadata for source {source_id}")
        
        db = SessionLocal()
        try:
            source = db.query(Source).filter(Source.id == source_id).first()
            if not source:
                logger.warning(f"Source not found: {source_id}")
                return {"error": "Source not found"}
            
            # Parse feed
            feed = feedparser.parse(source.url)
            
            # Update metadata
            if feed.feed:
                source.name = feed.feed.get("title", source.name)
                source.description = feed.feed.get("description", source.description)
                db.commit()
                
                logger.info(
                    f"Updated metadata for {source.name}",
                    extra={
                        "source_id": source_id,
                        "name": source.name,
                    }
                )
            
            return {
                "source_id": source_id,
                "name": source.name,
                "description": source.description,
            }
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Metadata refresh failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)

