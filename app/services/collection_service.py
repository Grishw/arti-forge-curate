import os
import shutil
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from app.repositories.collection_repository import CollectionRepository
from app.schemas.collection import CollectionCreate, CollectionUpdate, Collection
from app.core.config import settings

class CollectionService:
    def __init__(self):
        self.collection_repo = CollectionRepository()

    async def create_collection(self, collection_data: CollectionCreate) -> Collection:
        collection_id = str(uuid.uuid4())
        folder_path = os.path.join(settings.storage_root, "collections", collection_id)
        os.makedirs(folder_path, exist_ok=True)
        
        collection_dict = collection_data.model_dump()
        collection_dict['id'] = collection_id
        collection_dict['folder_path'] = folder_path
        collection_dict['created_at'] = datetime.utcnow().isoformat()
        new_collection = await self.collection_repo.create(collection_dict)
        return new_collection

    async def get_collection(self, collection_id: str) -> Collection:
        collection = await self.collection_repo.get(collection_id)
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        return collection

    async def list_collections(self, curator_id: Optional[str] = None, event_id: Optional[str] = None) -> List[Collection]:
        filters = {}
        if curator_id:
            filters['curator_id'] = curator_id
        if event_id:
            filters['event_id'] = event_id
        return await self.collection_repo.list(**filters)

    async def update_collection(self, collection_id: str, collection_data: CollectionUpdate) -> Collection:
        existing = await self.get_collection(collection_id)
        update_data = collection_data.model_dump(exclude_unset=True)
        updated = await self.collection_repo.update(collection_id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Collection not found")
        return updated

    async def delete_collection(self, collection_id: str) -> bool:
        collection = await self.get_collection(collection_id)
        folder_path = collection.folder_path
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        deleted = await self.collection_repo.delete(collection_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Collection not found")
        return True