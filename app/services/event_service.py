import os
import shutil
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventCreate, EventUpdate, Event
from app.core.config import settings

class EventService:
    def __init__(self):
        self.event_repo = EventRepository()

    async def create_event(self, event_data: EventCreate) -> Event:
        # Генерируем ID и создаём папку
        event_id = str(uuid.uuid4())
        folder_path = os.path.join(settings.storage_root, "events", event_id)
        os.makedirs(folder_path, exist_ok=True)
        
        # Подготавливаем данные
        event_dict = event_data.model_dump()
        event_dict['id'] = event_id
        event_dict['folder_path'] = folder_path
        event_dict['created_at'] = datetime.utcnow().isoformat()
        # Создаём запись в репозитории
        new_event = await self.event_repo.create(event_dict)
        return new_event

    async def get_event(self, event_id: str) -> Event:
        event = await self.event_repo.get(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event

    async def list_events(self, curator_id: Optional[str] = None, status: Optional[str] = None) -> List[Event]:
        filters = {}
        if curator_id:
            filters['curator_id'] = curator_id
        if status:
            filters['status'] = status
        return await self.event_repo.list(**filters)

    async def update_event(self, event_id: str, event_data: EventUpdate) -> Event:
        # Проверяем существование
        existing = await self.get_event(event_id)
        # Обновляем только переданные поля (исключаем None)
        update_data = event_data.model_dump(exclude_unset=True)
        updated = await self.event_repo.update(event_id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Event not found")
        return updated

    async def delete_event(self, event_id: str) -> bool:
        # Проверяем существование
        event = await self.get_event(event_id)
        # Удаляем папку события
        folder_path = event.folder_path
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        # Удаляем запись из репозитория
        deleted = await self.event_repo.delete(event_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Event not found")
        return True

    async def publish_event(self, event_id: str) -> Event:
        event = await self.get_event(event_id)
        if event.status == "published":
            raise HTTPException(status_code=400, detail="Event already published")
        updated = await self.event_repo.update(event_id, {"status": "published"})
        return updated

    async def search_events(self, query: str, curator_id: Optional[str] = None) -> List[Event]:
        # Все события (или с фильтром по куратору)
        events = await self.list_events(curator_id=curator_id)
        # Фильтруем по названию или описанию (регистронезависимо)
        q = query.lower()
        return [e for e in events if q in e.name.lower() or (e.description and q in e.description.lower())]