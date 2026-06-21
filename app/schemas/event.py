from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any

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

class MarkerImageInfo(BaseModel):
    marker_id: str
    image_url: str  # ссылка на эндпоинт для получения изображения
    anchor_params: Dict[str, Any]  # параметры привязки (planeType, physicalWidth и т.д.)
    attached_models: Optional[list] = None

class EventMarkersResponse(BaseModel):
    event_id: str
    works: Dict[str, List[MarkerImageInfo]]  # work_id -> список маркеро