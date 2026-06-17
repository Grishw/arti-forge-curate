from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    event_id: Optional[str] = None  # может быть привязана к событию
    curator_id: Optional[str] = None  # теперь необязательно
    folder_path: Optional[str] = None  # теперь необязательно

class CollectionCreate(CollectionBase):
    pass

class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    event_id: Optional[str] = None

class Collection(CollectionBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True