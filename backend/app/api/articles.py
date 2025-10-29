"""Articles API endpoints."""
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.core.db import get_db
from app.models import Article, Score
from app.core.llm import analyze_article
from app.core.strategies import map_to_strategy
from app.core.config import get_settings
from app.middleware.rate_limit import limiter
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/articles", tags=["articles"])


class ArticleResponse(BaseModel):
    """Article response schema."""
    id: int
    url: str
    title: str
    summary: Optional[str]
    source_name: str
    source_url: str
    source_type: str
    published_at: datetime
    ticker_guess: Optional[str]
    score: Optional[float] = None

    class Config:
        from_attributes = True


@router.get("", response_model=list[ArticleResponse])
@limiter.limit("30/minute")  # Rate limit: 30 requests per minute
def list_articles(
    request: Request,
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Search in title/summary"),
    min_score: float = Query(0, description="Minimum score"),
    ticker: Optional[str] = Query(None, description="Filter by ticker"),
    domain: Optional[str] = Query(None, description="Filter by source domain"),
    since: Optional[datetime] = Query(None, description="Articles since this time"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
) -> list[ArticleResponse]:
    """
    List articles with filtering and search.
    
    Query parameters:
    - q: Search in title/summary
    - min_score: Minimum score threshold
    - ticker: Filter by ticker symbol
    - domain: Filter by source domain
    - since: Articles published after this ISO timestamp
    - limit: Max results (default 100, max 1000)
    - offset: Pagination offset
    """
    query = db.query(Article, Score).outerjoin(Score, Article.id == Score.article_id)
    
    # Search filter
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Article.title.ilike(search_term),
                Article.summary.ilike(search_term),
            )
        )
    
    # Score filter
    if min_score > 0:
        query = query.filter(Score.total >= min_score)
    
    # Ticker filter
    if ticker:
        query = query.filter(Article.ticker_guess == ticker.upper())
    
    # Domain filter
    if domain:
        query = query.filter(Article.source_url.ilike(f"%{domain}%"))
    
    # Time filter
    if since:
        query = query.filter(Article.published_at >= since)
    
    # Order by published_at descending, then by score
    query = query.order_by(Article.published_at.desc())
    
    # Pagination
    results = query.limit(limit).offset(offset).all()
    
    response = []
    for article, score in results:
        article_dict = ArticleResponse.from_orm(article)
        if score:
            article_dict.score = score.total
        response.append(article_dict)
    
    return response


@router.get("/{article_id}", response_model=ArticleResponse)
@limiter.limit("30/minute")  # Rate limit: 30 requests per minute
def get_article(request: Request, article_id: int, db: Session = Depends(get_db)) -> ArticleResponse:
    """Get a single article by ID."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return ArticleResponse.from_orm(article)


@router.post("/llm/analyze/{article_id}")
@limiter.limit("30/minute")  # Rate limit: 30 requests per minute
def analyze_article_llm(
    request: Request,
    article_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Trigger LLM analysis for an article.

    This endpoint queues the analysis as a background task and returns immediately.
    The analysis results will be stored in the article's llm_plan, strategy_bucket,
    and strategy_risk fields.
    """
    if not settings.llm_enabled:
        raise HTTPException(
            status_code=503,
            detail="LLM analysis is not enabled. Please configure OPENAI_API_KEY."
        )

    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    def _run_analysis():
        """Background task to run LLM analysis."""
        try:
            # Get score if available
            score = db.query(Score).filter(Score.article_id == article_id).first()

            # Build payload for LLM
            payload = {
                "title": article.title,
                "summary": article.summary or "",
                "url": article.url,
                "source_name": article.source_name,
                "source_url": article.source_url,
                "published_at": article.published_at.isoformat() if article.published_at else "",
                "rule_catalyst": score.catalyst if score else 0,
                "rule_novelty": score.novelty if score else 0,
                "rule_credibility": score.credibility if score else 0,
            }

            # Run LLM analysis
            logger.info(f"Running LLM analysis for article {article_id}")
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

            logger.info(f"LLM analysis complete for article {article_id}: {strategy['bucket']}")

            # Generate trading signals
            try:
                from app.api.signals import ingest_article as generate_signals
                signal_payload = {
                    "article_id": article.id,
                    "title": article.title,
                    "summary": article.summary or "",
                    "full_text": "",  # Could add full text if available
                    "source_name": article.source_name,
                    "llm_plan": plan,
                }
                result = generate_signals(signal_payload)
                logger.info(f"Generated {result['count']} signals for article {article_id}")
            except Exception as sig_err:
                logger.error(f"Error generating signals for article {article_id}: {sig_err}")

        except Exception as e:
            logger.error(f"Error in LLM analysis background task: {e}")
            db.rollback()

    # Queue the analysis
    background_tasks.add_task(_run_analysis)

    return {"status": "queued", "article_id": article_id}


@router.get("/{article_id}/plan")
@limiter.limit("30/minute")  # Rate limit: 30 requests per minute
def get_article_plan(request: Request, article_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get the LLM analysis plan for an article.

    Returns the strategy bucket, risk parameters, and full LLM plan.
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if not article.llm_plan:
        raise HTTPException(
            status_code=404,
            detail="No LLM plan available for this article. Try analyzing it first."
        )

    return {
        "article_id": article.id,
        "strategy_bucket": article.strategy_bucket,
        "strategy_risk": article.strategy_risk,
        "llm_plan": article.llm_plan,
        "published_at": article.published_at.isoformat() if article.published_at else None,
    }

