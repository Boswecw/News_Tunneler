"""Sources API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
from app.core.db import get_db
from app.models import Source, SourceType
from app.core.logging import logger
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/sources", tags=["sources"])


class SourceCreate(BaseModel):
    """Source creation schema."""
    url: str
    name: str
    source_type: str = "rss"


class SourceResponse(BaseModel):
    """Source response schema."""
    id: int
    url: str
    name: str
    source_type: str
    enabled: bool
    created_at: datetime
    last_fetched_at: datetime | None

    class Config:
        from_attributes = True


@router.get("", response_model=list[SourceResponse])
def list_sources(db: Session = Depends(get_db)) -> list[SourceResponse]:
    """List all sources."""
    sources = db.query(Source).order_by(Source.created_at.desc()).all()
    return [SourceResponse.from_orm(s) for s in sources]


@router.post("", response_model=SourceResponse)
async def create_source(
    source: SourceCreate,
    db: Session = Depends(get_db),
) -> SourceResponse:
    """
    Create a new source.
    
    Validates that the feed URL is reachable before adding.
    """
    # Check if source already exists
    existing = db.query(Source).filter(Source.url == source.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Source already exists")
    
    # Validate URL is reachable
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.head(source.url, follow_redirects=True)
            response.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to validate source URL {source.url}: {e}")
        # Don't fail, just warn - some feeds may not support HEAD
    
    # Create source
    db_source = Source(
        url=source.url,
        name=source.name,
        source_type=source.source_type,
        enabled=True,
    )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    
    logger.info(f"Created source: {source.name} ({source.url})")
    return SourceResponse.from_orm(db_source)


@router.patch("/{source_id}", response_model=SourceResponse)
def update_source(
    source_id: int,
    enabled: bool | None = None,
    db: Session = Depends(get_db) = None,
) -> SourceResponse:
    """Update source (enable/disable)."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    if enabled is not None:
        source.enabled = enabled
    
    db.commit()
    db.refresh(source)
    return SourceResponse.from_orm(source)


@router.delete("/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)) -> dict:
    """Delete a source."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    db.delete(source)
    db.commit()
    
    logger.info(f"Deleted source: {source.name}")
    return {"message": "Source deleted"}

