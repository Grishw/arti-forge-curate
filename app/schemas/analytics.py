from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AnalyticsBase(BaseModel):
    event_id: Optional[str] = None
    work_id: Optional[str] = None
    date: datetime
    views: int = 0
    interactions: int = 0
    unique_users: int = 0

class AnalyticsCreate(AnalyticsBase):
    pass

class Analytics(AnalyticsBase):
    id: str

    class Config:
        from_attributes = True