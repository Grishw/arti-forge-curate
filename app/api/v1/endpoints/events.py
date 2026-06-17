from io import BytesIO
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.event import Event, EventCreate, EventUpdate
from app.services.event_service import EventService
from app.core.dependencies import get_current_curator_or_admin
from app.schemas.user import User
from app.schemas.event_work import EventWorkCreate, EventWorkUpdate
from app.services.assignment_service import AssignmentService
from fastapi.responses import StreamingResponse
import shutil
import zipfile

router = APIRouter()

@router.get("/", response_model=List[Event])
async def list_events(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = EventService()
    # Для куратора показываем только его события
    return await service.list_events(curator_id=current_user.id, status=status)

@router.post("/", response_model=Event)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = EventService()
    # Подставляем curator_id из текущего пользователя
    event_data.curator_id = current_user.id
    return await service.create_event(event_data)

@router.get("/{event_id}", response_model=Event)
async def get_event(
    event_id: str,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = EventService()
    event = await service.get_event(event_id)
    # Проверяем права: куратор видит только свои
    if current_user.role != "admin" and event.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your event")
    return event

@router.put("/{event_id}", response_model=Event)
async def update_event(
    event_id: str,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = EventService()
    # Проверяем существование и права
    event = await service.get_event(event_id)
    if current_user.role != "admin" and event.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your event")
    return await service.update_event(event_id, event_data)

@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = EventService()
    event = await service.get_event(event_id)
    if current_user.role != "admin" and event.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your event")
    await service.delete_event(event_id)
    return {"message": "Event deleted"}

@router.post("/{event_id}/publish", response_model=Event)
async def publish_event(
    event_id: str,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = EventService()
    event = await service.get_event(event_id)
    if current_user.role != "admin" and event.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your event")
    return await service.publish_event(event_id)

@router.get("/search", response_model=List[Event])
async def search_events(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = EventService()
    return await service.search_events(q, curator_id=current_user.id)

@router.post("/{event_id}/works")
async def add_work_to_event(
    event_id: str,
    data: EventWorkCreate,
    current_user: User = Depends(get_current_curator_or_admin)
):
    # Проверяем права на событие
    service = EventService()
    event = await service.get_event(event_id)
    if current_user.role != "admin" and event.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your event")
    
    assign_service = AssignmentService()
    return await assign_service.add_work_to_event(
        event_id=event_id,
        work_id=data.work_id,
        display_settings=data.display_settings,
        status=data.status
    )

@router.put("/{event_id}/works/{work_id}")
async def update_event_work(
    event_id: str,
    work_id: str,
    update_data: EventWorkUpdate,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = EventService()
    event = await service.get_event(event_id)
    if current_user.role != "admin" and event.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your event")
    
    assign_service = AssignmentService()
    return await assign_service.update_event_work_settings(event_id, work_id, update_data)

@router.delete("/{event_id}/works/{work_id}")
async def remove_work_from_event(
    event_id: str,
    work_id: str,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = EventService()
    event = await service.get_event(event_id)
    if current_user.role != "admin" and event.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your event")
    
    assign_service = AssignmentService()
    await assign_service.remove_work_from_event(event_id, work_id)
    return {"message": "Work removed from event"}

@router.patch("/{event_id}/works/{work_id}/status")
async def update_event_work_status(
    event_id: str,
    work_id: str,
    status: str,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = EventService()
    event = await service.get_event(event_id)
    if current_user.role != "admin" and event.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your event")
    
    assign_service = AssignmentService()
    update_data = EventWorkUpdate(status=status)
    return await assign_service.update_event_work_settings(event_id, work_id, update_data)

@router.get("/{event_id}/download")
async def download_event(
    event_id: str,
    # можно сделать публичным для Lens
):
    service = EventService()
    event = await service.get_event(event_id)
    if event.status != "published":
        # Можно разрешить скачивать только опубликованные, или если куратор свой
        # Для простоты разрешим всем
        pass
    folder_path = event.folder_path
    # Создаём zip-архив на лету
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zip_file.write(file_path, arcname)
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=event_{event_id}.zip"}
    )

@router.get("/public", response_model=List[Event])
async def list_public_events(status: Optional[str] = "published"):
    """Публичный список событий (для Lens)"""
    service = EventService()
    # Возвращаем только опубликованные события, без привязки к куратору
    return await service.list_events(status=status)

@router.get("/public/search", response_model=List[Event])
async def search_public_events(q: str = Query(..., min_length=1)):
    """Публичный поиск (для Lens)"""
    service = EventService()
    # Ищем по всем опубликованным событиям
    events = await service.list_events(status="published")
    q_lower = q.lower()
    return [e for e in events if q_lower in e.name.lower() or (e.description and q_lower in e.description.lower())]

@router.get("/{event_id}/download", response_class=StreamingResponse)
async def download_event_public(event_id: str):
    """Публичное скачивание события (для Lens)"""
    service = EventService()
    event = await service.get_event(event_id)
    # Можно разрешить скачивать только опубликованные
    if event.status != "published":
        raise HTTPException(403, "Event not published")
    folder_path = event.folder_path
    if not os.path.exists(folder_path):
        raise HTTPException(404, "Event folder not found")

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zip_file.write(file_path, arcname)
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=event_{event_id}.zip"}
    )