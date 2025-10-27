"""Articles API endpoints."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.core.db import get_db
from app.models import Article, Score
from pydantic import BaseModel

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
def list_articles(
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
def get_article(article_id: int, db: Session = Depends(get_db)) -> ArticleResponse:
    """Get a single article by ID."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Article not found")
    
    return ArticleResponse.from_orm(article)

