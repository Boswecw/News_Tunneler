"""Seed database with initial data."""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.db import get_db_context, engine
from app.models import Base, Source, Article, Score, Setting
from app.core.scoring import (
    score_catalyst,
    score_novelty,
    score_credibility,
    compute_total_score,
)
from app.core.sentiment import analyze_sentiment
from app.core.tickers import extract_ticker


def load_json(filename: str) -> dict:
    """Load JSON file from seeds directory."""
    path = Path(__file__).parent / filename
    with open(path) as f:
        return json.load(f)


def seed_sources(db: Session) -> None:
    """Seed sources from seed_sources.json."""
    data = load_json("seed_sources.json")
    
    for source_data in data["sources"]:
        # Check if already exists
        existing = db.query(Source).filter(Source.url == source_data["url"]).first()
        if existing:
            print(f"Source already exists: {source_data['name']}")
            continue
        
        source = Source(
            url=source_data["url"],
            name=source_data["name"],
            source_type=source_data["type"],
            enabled=True,
        )
        db.add(source)
        print(f"Added source: {source_data['name']}")
    
    db.commit()


def seed_articles(db: Session) -> None:
    """Seed articles from seed_articles.json."""
    data = load_json("seed_articles.json")
    
    # Get settings for weights
    setting = db.query(Setting).filter(Setting.id == 1).first()
    if not setting:
        setting = Setting(id=1)
        db.add(setting)
        db.flush()
    
    weights = {
        "catalyst": setting.weight_catalyst,
        "novelty": setting.weight_novelty,
        "credibility": setting.weight_credibility,
        "sentiment": setting.weight_sentiment,
        "liquidity": setting.weight_liquidity,
    }
    
    now = datetime.now(timezone.utc)
    
    for i, article_data in enumerate(data["articles"]):
        # Check if already exists
        existing = db.query(Article).filter(Article.url == article_data["url"]).first()
        if existing:
            print(f"Article already exists: {article_data['title'][:50]}")
            continue
        
        # Vary published_at to test novelty scoring
        published_at = now - timedelta(hours=i % 48)
        
        article = Article(
            url=article_data["url"],
            title=article_data["title"],
            summary=article_data["summary"],
            source_name=article_data["source_name"],
            source_url=article_data["source_url"],
            source_type=article_data["source_type"],
            published_at=published_at,
            ticker_guess=article_data.get("ticker_guess"),
        )
        db.add(article)
        db.flush()
        
        # Compute scores
        catalyst = score_catalyst(article.title, article.summary)
        novelty = score_novelty(article.published_at)
        credibility = score_credibility(article.source_url)
        sentiment = analyze_sentiment(f"{article.title} {article.summary}")
        liquidity = 0.0
        
        total = compute_total_score(
            catalyst, novelty, credibility, sentiment, liquidity, weights
        )
        
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
        print(f"Added article: {article.title[:50]}... (score: {total:.1f})")
    
    db.commit()


def seed_settings(db: Session) -> None:
    """Ensure default settings exist."""
    setting = db.query(Setting).filter(Setting.id == 1).first()
    if not setting:
        setting = Setting(id=1)
        db.add(setting)
        db.commit()
        print("Created default settings")
    else:
        print("Settings already exist")


def main() -> None:
    """Run all seed functions."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    with get_db_context() as db:
        print("\nSeeding settings...")
        seed_settings(db)
        
        print("\nSeeding sources...")
        seed_sources(db)
        
        print("\nSeeding articles...")
        seed_articles(db)
    
    print("\n✅ Database seeding complete!")


if __name__ == "__main__":
    main()

