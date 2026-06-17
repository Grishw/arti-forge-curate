from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, Dict, Any

class CollectionWorkBase(BaseModel):
    collection_id: str
    work_id: str
    display_settings: Dict[str, Any] = {}
    status: str = "pending"

class CollectionWorkCreate(CollectionWorkBase):
    pass

class CollectionWorkUpdate(BaseModel):
    display_settings: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class CollectionWork(CollectionWorkBase):
    id: str
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True