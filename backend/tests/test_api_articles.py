"""Tests for articles API."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from app.main import app
from app.models import Base, Article, Score
from app.core.db import get_db

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override get_db dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture
def db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """Create test client."""
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_list_articles_empty(client):
    """Test listing articles when empty."""
    response = client.get("/api/articles")
    assert response.status_code == 200
    assert response.json() == []


def test_list_articles_with_data(client):
    """Test listing articles with data."""
    db = TestingSessionLocal()
    
    # Create articles
    now = datetime.utcnow()
    for i in range(3):
        article = Article(
            url=f"https://example.com/article{i}",
            title=f"Test Article {i}",
            summary=f"Summary {i}",
            source_name="Test Source",
            source_url="https://example.com",
            source_type="rss",
            published_at=now - timedelta(hours=i),
            ticker_guess="AAPL" if i == 0 else None,
        )
        db.add(article)
        db.flush()
        
        # Add score
        score = Score(
            article_id=article.id,
            catalyst=5.0,
            novelty=5.0,
            credibility=5.0,
            sentiment=4.0,
            liquidity=0.0,
            total=19.0 if i == 0 else 10.0,
        )
        db.add(score)
    
    db.commit()
    db.close()
    
    response = client.get("/api/articles")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_filter_by_min_score(client):
    """Test filtering articles by minimum score."""
    db = TestingSessionLocal()
    
    now = datetime.utcnow()
    article = Article(
        url="https://example.com/article1",
        title="Test Article",
        summary="Summary",
        source_name="Test Source",
        source_url="https://example.com",
        source_type="rss",
        published_at=now,
    )
    db.add(article)
    db.flush()
    
    score = Score(
        article_id=article.id,
        catalyst=5.0,
        novelty=5.0,
        credibility=5.0,
        sentiment=4.0,
        liquidity=0.0,
        total=19.0,
    )
    db.add(score)
    db.commit()
    db.close()
    
    # Should return article with score >= 15
    response = client.get("/api/articles?min_score=15")
    assert response.status_code == 200
    assert len(response.json()) == 1
    
    # Should not return article with score < 20
    response = client.get("/api/articles?min_score=20")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_filter_by_ticker(client):
    """Test filtering articles by ticker."""
    db = TestingSessionLocal()
    
    now = datetime.utcnow()
    article = Article(
        url="https://example.com/article1",
        title="Test Article",
        summary="Summary",
        source_name="Test Source",
        source_url="https://example.com",
        source_type="rss",
        published_at=now,
        ticker_guess="AAPL",
    )
    db.add(article)
    db.commit()
    db.close()
    
    response = client.get("/api/articles?ticker=AAPL")
    assert response.status_code == 200
    assert len(response.json()) == 1
    
    response = client.get("/api/articles?ticker=MSFT")
    assert response.status_code == 200
    assert len(response.json()) == 0

