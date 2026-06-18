from io import BytesIO
import os
import zipfile

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from fastapi.responses import StreamingResponse
from app.repositories.collection_work_repository import CollectionWorkRepository
from app.repositories.work_repository import WorkRepository
from app.schemas.collection import Collection, CollectionCreate, CollectionUpdate
from app.services.collection_service import CollectionService
from app.core.dependencies import get_current_curator_or_admin
from app.schemas.user import User
from app.schemas.collection_work import CollectionWorkCreate, CollectionWorkUpdate
from app.services.assignment_service import AssignmentService
from app.services.collection_service import CollectionService
from app.services.event_service import EventService

router = APIRouter()

@router.get("/", response_model=List[Collection])
async def list_collections(
    event_id: Optional[str] = None,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = CollectionService()
    return await service.list_collections(curator_id=current_user.id, event_id=event_id)

@router.post("/", response_model=Collection)
async def create_collection(
    collection_data: CollectionCreate,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = CollectionService()
    collection_data.curator_id = current_user.id
    return await service.create_collection(collection_data)

@router.get("/{collection_id}", response_model=Collection)
async def get_collection(
    collection_id: str,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = CollectionService()
    collection = await service.get_collection(collection_id)
    if current_user.role != "admin" and collection.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your collection")
    return collection

@router.put("/{collection_id}", response_model=Collection)
async def update_collection(
    collection_id: str,
    collection_data: CollectionUpdate,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = CollectionService()
    collection = await service.get_collection(collection_id)
    if current_user.role != "admin" and collection.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your collection")
    return await service.update_collection(collection_id, collection_data)

@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = CollectionService()
    collection = await service.get_collection(collection_id)
    if current_user.role != "admin" and collection.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your collection")
    await service.delete_collection(collection_id)
    return {"message": "Collection deleted"}

@router.post("/{collection_id}/works")
async def add_work_to_collection(
    collection_id: str,
    data: CollectionWorkCreate,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = CollectionService()
    collection = await service.get_collection(collection_id)
    if current_user.role != "admin" and collection.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your collection")
    
    assign_service = AssignmentService()
    return await assign_service.add_work_to_collection(
        collection_id=collection_id,
        work_id=data.work_id,
        display_settings=data.display_settings,
        status=data.status
    )

@router.delete("/{collection_id}/works/{work_id}")
async def remove_work_from_collection(
    collection_id: str,
    work_id: str,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = CollectionService()
    collection = await service.get_collection(collection_id)
    if current_user.role != "admin" and collection.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your collection")
    
    assign_service = AssignmentService()
    await assign_service.remove_work_from_collection(collection_id, work_id)
    return {"message": "Work removed from collection"}

@router.put("/{collection_id}/works/{work_id}")
async def update_collection_work(
    collection_id: str,
    work_id: str,
    update_data: CollectionWorkUpdate,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = CollectionService()
    collection = await service.get_collection(collection_id)
    if current_user.role != "admin" and collection.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your collection")
    
    assign_service = AssignmentService()
    return await assign_service.update_collection_work_settings(collection_id, work_id, update_data)

@router.patch("/{collection_id}/works/{work_id}/status")
async def update_collection_work_status(
    collection_id: str,
    work_id: str,
    status: str,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = CollectionService()
    collection = await service.get_collection(collection_id)
    if current_user.role != "admin" and collection.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your collection")
    
    assign_service = AssignmentService()
    update_data = CollectionWorkUpdate(status=status)
    return await assign_service.update_collection_work_settings(collection_id, work_id, update_data)

@router.get("/{collection_id}/download")
async def download_collection(collection_id: str):
    service = CollectionService()
    collection = await service.get_collection(collection_id)
    # (опционально) проверяем, что коллекция опубликована, если нужно
    folder_path = collection.folder_path
    if not os.path.exists(folder_path):
        raise HTTPException(404, "Collection folder not found")

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
        headers={"Content-Disposition": f"attachment; filename=collection_{collection_id}.zip"}
    )

# Приватные эндпоинты (требуют авторизации) – без изменений
@router.get("/", response_model=List[Collection])
async def list_collections(
    event_id: Optional[str] = None,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = CollectionService()
    return await service.list_collections(curator_id=current_user.id, event_id=event_id)

@router.post("/", response_model=Collection)
async def create_collection(
    collection_data: CollectionCreate,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = CollectionService()
    collection_data.curator_id = current_user.id
    return await service.create_collection(collection_data)

@router.get("/{collection_id}", response_model=Collection)
async def get_collection(
    collection_id: str,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = CollectionService()
    collection = await service.get_collection(collection_id)
    if current_user.role != "admin" and collection.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your collection")
    return collection

@router.put("/{collection_id}", response_model=Collection)
async def update_collection(
    collection_id: str,
    collection_data: CollectionUpdate,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = CollectionService()
    collection = await service.get_collection(collection_id)
    if current_user.role != "admin" and collection.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your collection")
    return await service.update_collection(collection_id, collection_data)

@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str,
    current_user: User = Depends(get_current_curator_or_admin)
):
    service = CollectionService()
    collection = await service.get_collection(collection_id)
    if current_user.role != "admin" and collection.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your collection")
    await service.delete_collection(collection_id)
    return {"message": "Collection deleted"}

# --- Публичный эндпоинт для скачивания (без JWT) ---
@router.get("/{collection_id}/download")
async def download_collection_public(collection_id: str):
    """
    Публичное скачивание коллекции для ARTi Lens.
    Доступно только если коллекция привязана к опубликованному событию.
    """
    service = CollectionService()
    collection = await service.get_collection(collection_id)
    
    # Проверяем доступность
    if collection.event_id:
        event_service = EventService()
        event = await event_service.get_event(collection.event_id)
        if event.status != "published":
            raise HTTPException(status_code=403, detail="Collection is not available (event not published)")
    else:
        # Если коллекция не привязана к событию, считаем её недоступной для публичного скачивания
        raise HTTPException(status_code=403, detail="Collection is not associated with a published event")
    
    folder_path = collection.folder_path
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail="Collection folder not found")

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
        headers={"Content-Disposition": f"attachment; filename=collection_{collection_id}.zip"}
    )

@router.get("/{collection_id}/works")
async def get_collection_works(
    collection_id: str,
    current_user: User = Depends(get_current_curator_or_admin)
):
    """Возвращает список EventWork для события, включая информацию о работе."""
    service = CollectionService()
    # Проверяем существование события и права
    event = await service.get_collection(collection_id)
    if current_user.role != "admin" and event.curator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your event")
    
    # Получаем все CollectionWork для этого события
    event_work_repo = CollectionWorkRepository()
    event_works = await event_work_repo.list(collection_id=collection_id)
    
    # Для каждого получаем детали работы (можно сделать одним запросом, но для простоты – цикл)
    result = []
    for ew in event_works:
        work_repo = WorkRepository()
        work = await work_repo.get(ew.work_id)
        result.append({
            **ew.model_dump(),
            'work': work.model_dump() if work else None
        })
    return result