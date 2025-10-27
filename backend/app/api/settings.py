"""Settings API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models import Setting
from pydantic import BaseModel

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingUpdate(BaseModel):
    """Settings update schema."""
    weight_catalyst: float | None = None
    weight_novelty: float | None = None
    weight_credibility: float | None = None
    weight_sentiment: float | None = None
    weight_liquidity: float | None = None
    min_alert_score: float | None = None
    poll_interval_sec: int | None = None


class SettingResponse(BaseModel):
    """Settings response schema."""
    weight_catalyst: float
    weight_novelty: float
    weight_credibility: float
    weight_sentiment: float
    weight_liquidity: float
    min_alert_score: float
    poll_interval_sec: int

    class Config:
        from_attributes = True


def get_or_create_setting(db: Session) -> Setting:
    """Get or create singleton setting."""
    setting = db.query(Setting).filter(Setting.id == 1).first()
    if not setting:
        setting = Setting(id=1)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


@router.get("", response_model=SettingResponse)
def get_settings(db: Session = Depends(get_db)) -> SettingResponse:
    """Get current settings."""
    setting = get_or_create_setting(db)
    return SettingResponse.from_orm(setting)


@router.patch("", response_model=SettingResponse)
def update_settings(
    update: SettingUpdate,
    db: Session = Depends(get_db),
) -> SettingResponse:
    """Update settings."""
    setting = get_or_create_setting(db)
    
    # Update only provided fields
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(setting, key, value)
    
    db.commit()
    db.refresh(setting)
    return SettingResponse.from_orm(setting)

