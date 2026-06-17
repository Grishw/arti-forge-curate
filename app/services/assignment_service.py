import os
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.repositories.event_work_repository import EventWorkRepository
from app.repositories.collection_work_repository import CollectionWorkRepository
from app.repositories.work_repository import WorkRepository
from app.repositories.event_repository import EventRepository
from app.repositories.collection_repository import CollectionRepository
from app.schemas.event_work import EventWorkCreate, EventWorkUpdate
from app.schemas.collection_work import CollectionWorkCreate, CollectionWorkUpdate
from app.utils.event_packager import EventPackager

class AssignmentService:
    def __init__(self):
        self.event_work_repo = EventWorkRepository()
        self.collection_work_repo = CollectionWorkRepository()
        self.work_repo = WorkRepository()
        self.event_repo = EventRepository()
        self.collection_repo = CollectionRepository()

    # -------- Работа с событиями --------

    async def add_work_to_event(
        self,
        event_id: str,
        work_id: str,
        display_settings: Dict[str, Any],
        status: str = "pending"
    ) -> Dict[str, Any]:
        """
        Добавляет работу в событие: создаёт EventWork, копирует файлы в папку события,
        обновляет manifest.
        """
        # Проверяем, существует ли событие
        event = await self.event_repo.get(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Проверяем, существует ли работа
        work = await self.work_repo.get(work_id)
        if not work:
            raise HTTPException(status_code=404, detail="Work not found")
        
        # Проверяем, не добавлена ли уже работа
        existing = await self.event_work_repo.list(event_id=event_id, work_id=work_id)
        if existing:
            raise HTTPException(status_code=400, detail="Work already added to this event")
        
        # Создаём запись EventWork
        event_work_data = EventWorkCreate(
            event_id=event_id,
            work_id=work_id,
            display_settings=display_settings,
            status=status
        )
        new_event_work = await self.event_work_repo.create(event_work_data.model_dump())
        
        # Если статус "approved" — копируем файлы в папку события и обновляем manifest
        if status == "approved":
            await self._sync_work_to_event_folder(event_id, work_id, display_settings)
        
        return new_event_work.model_dump()

    async def update_event_work_settings(
        self,
        event_id: str,
        work_id: str,
        update_data: EventWorkUpdate
    ) -> Optional[Dict[str, Any]]:
        """
        Обновляет настройки отображения или статус работы в событии.
        """
        # Находим связь
        items = await self.event_work_repo.list(event_id=event_id, work_id=work_id)
        if not items:
            raise HTTPException(status_code=404, detail="Work not found in this event")
        event_work = items[0]
        
        # Обновляем
        updated = await self.event_work_repo.update(
            event_work.id,
            update_data.model_dump(exclude_unset=True)
        )
        if not updated:
            raise HTTPException(status_code=404, detail="EventWork not found")
        
        # Если статус изменился на "approved" — копируем файлы
        if update_data.status == "approved":
            work = await self.work_repo.get(work_id)
            await self._sync_work_to_event_folder(
                event_id,
                work_id,
                updated.display_settings if hasattr(updated, 'display_settings') else {}
            )
        elif update_data.status in ["pending", "rejected"]:
            # Удаляем файлы работы из папки события
            await self._remove_work_from_event_folder(event_id, work_id)
        
        return updated.model_dump()

    async def remove_work_from_event(self, event_id: str, work_id: str) -> bool:
        """
        Удаляет работу из события.
        """
        items = await self.event_work_repo.list(event_id=event_id, work_id=work_id)
        if not items:
            raise HTTPException(status_code=404, detail="Work not found in this event")
        event_work = items[0]
        
        # Удаляем файлы из папки события
        await self._remove_work_from_event_folder(event_id, work_id)
        
        # Удаляем запись
        deleted = await self.event_work_repo.delete(event_work.id)
        if not deleted:
            raise HTTPException(status_code=404, detail="EventWork not found")
        return True

    async def _sync_work_to_event_folder(self, event_id: str, work_id: str, display_settings: Dict[str, Any]) -> None:
        """Копирует файлы работы в папку события и обновляет manifest."""
        event = await self.event_repo.get(event_id)
        if not event:
            return
        
        work = await self.work_repo.get(work_id)
        if not work:
            return
        
        packager = EventPackager(event.folder_path)
        await packager.add_work(work_id, work.zip_path, display_settings)

    async def _remove_work_from_event_folder(self, event_id: str, work_id: str) -> None:
        """Удаляет файлы работы из папки события."""
        event = await self.event_repo.get(event_id)
        if not event:
            return
        
        packager = EventPackager(event.folder_path)
        await packager.remove_work(work_id)

    # -------- Аналогично для коллекций (упрощённо) --------

    async def add_work_to_collection(
        self,
        collection_id: str,
        work_id: str,
        display_settings: Dict[str, Any],
        status: str = "pending"
    ) -> Dict[str, Any]:
        """Добавляет работу в коллекцию."""
        collection = await self.collection_repo.get(collection_id)
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        work = await self.work_repo.get(work_id)
        if not work:
            raise HTTPException(status_code=404, detail="Work not found")
        
        existing = await self.collection_work_repo.list(collection_id=collection_id, work_id=work_id)
        if existing:
            raise HTTPException(status_code=400, detail="Work already in collection")
        
        collection_work_data = CollectionWorkCreate(
            collection_id=collection_id,
            work_id=work_id,
            display_settings=display_settings,
            status=status
        )
        new_cw = await self.collection_work_repo.create(collection_work_data.model_dump())
        
        if status == "approved":
            await self._sync_work_to_collection_folder(collection_id, work_id, display_settings)
        
        return new_cw.model_dump()

    async def remove_work_from_collection(self, collection_id: str, work_id: str) -> bool:
        """Удаляет работу из коллекции."""
        items = await self.collection_work_repo.list(collection_id=collection_id, work_id=work_id)
        if not items:
            raise HTTPException(status_code=404, detail="Work not in collection")
        cw = items[0]
        
        await self._remove_work_from_collection_folder(collection_id, work_id)
        deleted = await self.collection_work_repo.delete(cw.id)
        return deleted

    async def _sync_work_to_collection_folder(self, collection_id: str, work_id: str, display_settings: Dict[str, Any]) -> None:
        """Копирует файлы работы в папку коллекции."""
        collection = await self.collection_repo.get(collection_id)
        if not collection:
            return
        
        work = await self.work_repo.get(work_id)
        if not work:
            return
        
        packager = EventPackager(collection.folder_path)  # та же логика
        await packager.add_work(work_id, work.zip_path, display_settings)

    async def _remove_work_from_collection_folder(self, collection_id: str, work_id: str) -> None:
        collection = await self.collection_repo.get(collection_id)
        if not collection:
            return
        packager = EventPackager(collection.folder_path)
        await packager.remove_work(work_id)

async def update_collection_work_settings(
    self,
    collection_id: str,
    work_id: str,
    update_data: CollectionWorkUpdate
) -> Optional[Dict[str, Any]]:
    """
    Обновляет настройки отображения или статус работы в коллекции.
    """
    items = await self.collection_work_repo.list(collection_id=collection_id, work_id=work_id)
    if not items:
        raise HTTPException(status_code=404, detail="Work not found in this collection")
    collection_work = items[0]

    updated = await self.collection_work_repo.update(
        collection_work.id,
        update_data.model_dump(exclude_unset=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="CollectionWork not found")

    # Если статус изменился на "approved" — копируем файлы
    if update_data.status == "approved":
        work = await self.work_repo.get(work_id)
        await self._sync_work_to_collection_folder(
            collection_id,
            work_id,
            updated.display_settings if hasattr(updated, 'display_settings') else {}
        )
    elif update_data.status in ["pending", "rejected"]:
        # Удаляем файлы работы из папки коллекции
        await self._remove_work_from_collection_folder(collection_id, work_id)

    return updated.model_dump()