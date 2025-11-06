"""
Research feature storage service.

Captures frozen feature snapshots at article publish time
to guarantee no look-ahead bias.
"""
import json
from datetime import datetime, timezone
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.models.research import ResearchFeatures
from app.ml.features import featurize, validate_features
from app.core.logging import logger


def store_features(
    db: Session,
    article_id: str,
    symbol: str,
    published_at: str,
    analysis_payload: Dict[str, Any]
) -> bool:
    """
    Store frozen feature snapshot for an article.
    
    Args:
        db: Database session
        article_id: Unique article identifier
        symbol: Stock ticker
        published_at: ISO8601 timestamp of article publication
        analysis_payload: Full analysis dict with technical + LLM features
        
    Returns:
        True if features were stored successfully
    """
    try:
        # Extract features using consistent featurizer
        features = featurize(analysis_payload)
        
        # Validate features
        if not validate_features(features):
            logger.warning(f"Insufficient features for article {article_id}, skipping storage")
            return False
        
        # Create or update feature snapshot
        feature_row = ResearchFeatures(
            article_id=article_id,
            symbol=symbol.upper(),
            published_at=published_at,
            features_json=json.dumps(features),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        db.merge(feature_row)
        db.commit()
        
        logger.info(f"Stored features for article {article_id} ({symbol})")
        return True
        
    except Exception as e:
        logger.error(f"Error storing features for article {article_id}: {e}")
        db.rollback()
        return False


def get_features(db: Session, article_id: str) -> Dict[str, Any]:
    """
    Retrieve stored features for an article.
    
    Args:
        db: Database session
        article_id: Article identifier
        
    Returns:
        Feature dict or empty dict if not found
    """
    try:
        row = db.query(ResearchFeatures).filter(
            ResearchFeatures.article_id == article_id
        ).first()
        
        if row:
            return json.loads(row.features_json)
        
        return {}
        
    except Exception as e:
        logger.error(f"Error retrieving features for article {article_id}: {e}")
        return {}

