from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class WorkBase(BaseModel):
    external_id: str
    author_id: str
    name: str
    description: Optional[str] = None
    preview_path: Optional[str] = None
    zip_path: str
    metadata: Dict[str, Any] = {}  # project.json + export.json

class WorkCreate(WorkBase):
    pass

class WorkUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Work(WorkBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True