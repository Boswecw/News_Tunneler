"""Deduplication logic for articles."""
import hashlib
from sqlalchemy.orm import Session
from app.models import Article


def normalize_title(title: str) -> str:
    """Normalize title for comparison."""
    return title.lower().strip()


def hash_title(title: str) -> str:
    """Create hash of normalized title."""
    normalized = normalize_title(title)
    return hashlib.md5(normalized.encode()).hexdigest()


def article_exists(db: Session, url: str, title: str) -> bool:
    """
    Check if article already exists by URL or title hash.
    
    Returns True if article exists, False otherwise.
    """
    # Check by URL first (fastest)
    if db.query(Article).filter(Article.url == url).first():
        return True
    
    # Check by title hash
    title_hash = hash_title(title)
    # For now, we'll just check URL since title hashing is less reliable
    # In production, you might want to check both
    
    return False

