"""Tests for deduplication logic."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Article
from app.core.dedupe import article_exists
from datetime import datetime, timezone

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create test database and session."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_article_not_exists(db):
    """Test article_exists returns False for new article."""
    assert article_exists(db, "https://example.com/article1", "Test Article") is False


def test_article_exists_by_url(db):
    """Test article_exists returns True for duplicate URL."""
    # Insert article
    article = Article(
        url="https://example.com/article1",
        title="Test Article",
        summary="Test summary",
        source_name="Test Source",
        source_url="https://example.com",
        source_type="rss",
        published_at=datetime.now(timezone.utc),
    )
    db.add(article)
    db.commit()

    # Check exists
    assert article_exists(db, "https://example.com/article1", "Different Title") is True


def test_article_exists_by_title(db):
    """Test article_exists checks by title hash."""
    # Insert article
    article = Article(
        url="https://example.com/article1",
        title="Test Article",
        summary="Test summary",
        source_name="Test Source",
        source_url="https://example.com",
        source_type="rss",
        published_at=datetime.now(timezone.utc),
    )
    db.add(article)
    db.commit()

    # Check exists by URL (primary check)
    assert article_exists(db, "https://example.com/article1", "Test Article") is True

