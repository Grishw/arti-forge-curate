from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, Dict, Any

class EventWorkBase(BaseModel):
    event_id: str
    work_id: str
    display_settings: Dict[str, Any] = {}  # scale, position, rotation
    status: str = "pending"  # pending, approved, rejected

class EventWorkCreate(EventWorkBase):
    pass

class EventWorkUpdate(BaseModel):
    display_settings: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class EventWork(EventWorkBase):
    id: str
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True