"""
LLM Analysis Tasks

Celery tasks for asynchronous LLM-based article analysis.
"""
from typing import Dict, Any
from app.core.celery_app import celery_app
from app.core.llm import analyze_article
from app.core.structured_logging import get_logger
from app.core.feature_flags import is_feature_enabled, FeatureFlag

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.llm_tasks.analyze_article_async",
    max_retries=3,
    default_retry_delay=60,  # Retry after 1 minute
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes
    retry_jitter=True,
)
def analyze_article_async(self, article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze an article using LLM asynchronously.
    
    Args:
        article: Article data dictionary
        
    Returns:
        Analysis results with catalyst, novelty, credibility scores
    """
    # Check if LLM analysis is enabled
    if not is_feature_enabled(FeatureFlag.LLM_ANALYSIS):
        logger.warning("LLM analysis is disabled via feature flag")
        return {
            "catalyst": 0.0,
            "novelty": 0.0,
            "credibility": 0.0,
            "error": "LLM analysis disabled"
        }
    
    try:
        logger.info(
            f"Analyzing article: {article.get('title', 'Unknown')[:50]}...",
            extra={
                "article_id": article.get("id"),
                "ticker": article.get("ticker"),
                "source": article.get("source"),
            }
        )
        
        # Perform LLM analysis
        result = analyze_article(article)
        
        logger.info(
            "Article analysis complete",
            extra={
                "article_id": article.get("id"),
                "catalyst": result.get("catalyst"),
                "novelty": result.get("novelty"),
                "credibility": result.get("credibility"),
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"LLM analysis failed: {str(e)}",
            exc_info=True,
            extra={
                "article_id": article.get("id"),
                "error": str(e),
            }
        )
        
        # Retry the task
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    name="app.tasks.llm_tasks.batch_analyze_articles",
    max_retries=2,
    default_retry_delay=120,
)
def batch_analyze_articles(self, articles: list[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze multiple articles in batch.
    
    Args:
        articles: List of article dictionaries
        
    Returns:
        Summary of batch analysis results
    """
    if not is_feature_enabled(FeatureFlag.LLM_ANALYSIS):
        logger.warning("LLM analysis is disabled via feature flag")
        return {
            "total": len(articles),
            "analyzed": 0,
            "failed": 0,
            "error": "LLM analysis disabled"
        }
    
    try:
        logger.info(f"Starting batch analysis of {len(articles)} articles")
        
        results = []
        failed = 0
        
        for article in articles:
            try:
                # Queue individual analysis tasks
                task = analyze_article_async.delay(article)
                results.append({
                    "article_id": article.get("id"),
                    "task_id": task.id,
                    "status": "queued"
                })
            except Exception as e:
                logger.error(f"Failed to queue article {article.get('id')}: {e}")
                failed += 1
        
        logger.info(
            f"Batch analysis queued: {len(results)} tasks, {failed} failed",
            extra={
                "total": len(articles),
                "queued": len(results),
                "failed": failed,
            }
        )
        
        return {
            "total": len(articles),
            "queued": len(results),
            "failed": failed,
            "tasks": results,
        }
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    name="app.tasks.llm_tasks.reanalyze_low_score_articles",
    max_retries=1,
)
def reanalyze_low_score_articles(self, min_score: float = 3.0) -> Dict[str, Any]:
    """
    Re-analyze articles with low scores to improve accuracy.
    
    Args:
        min_score: Minimum score threshold for re-analysis
        
    Returns:
        Summary of re-analysis results
    """
    try:
        from app.core.db import SessionLocal
        from app.models.signal import Signal
        
        logger.info(f"Re-analyzing articles with score < {min_score}")
        
        # Get low-score signals
        db = SessionLocal()
        try:
            low_score_signals = db.query(Signal).filter(
                Signal.total_score < min_score
            ).limit(100).all()
            
            logger.info(f"Found {len(low_score_signals)} low-score signals")
            
            # Queue re-analysis tasks
            tasks = []
            for signal in low_score_signals:
                article_data = {
                    "id": signal.id,
                    "title": signal.title,
                    "content": signal.content,
                    "ticker": signal.ticker,
                    "source": signal.source,
                }
                
                task = analyze_article_async.delay(article_data)
                tasks.append(task.id)
            
            return {
                "total": len(low_score_signals),
                "queued": len(tasks),
                "task_ids": tasks,
            }
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Re-analysis failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)

