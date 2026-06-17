from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EventBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    status: str = "draft"  # draft, published, archived
    curator_id: Optional[str] = None  # теперь необязательно
    folder_path: Optional[str] = None  # теперь необязательно

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    status: Optional[str] = None

class Event(EventBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True