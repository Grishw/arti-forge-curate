import os
import shutil
import uuid
from typing import List, Optional
from fastapi import HTTPException, UploadFile
from app.repositories.work_repository import WorkRepository
from app.repositories.author_repository import AuthorRepository
from app.schemas.work import WorkCreate, Work
from app.schemas.author import AuthorCreate
from app.core.config import settings
from app.utils.zip_reader import read_work_metadata
import asyncio
import aiofiles

class WorkService:
    def __init__(self):
        self.work_repo = WorkRepository()
        self.author_repo = AuthorRepository()

    async def ingest_work(
        self,
        file: UploadFile,
        external_id: str,
        author_name: str,
        author_email: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Work:
        # 1. Сохраняем zip-архив
        zip_filename = f"{uuid.uuid4()}.zip"
        zip_path = os.path.join(settings.storage_root, "zips", zip_filename)
        async with aiofiles.open(zip_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        try:
            # 2. Читаем метаданные
            metadata, preview_path_in_zip = await read_work_metadata(zip_path)

            # 3. Извлекаем preview, если есть
            preview_path = None
            if preview_path_in_zip:
                preview_ext = os.path.splitext(preview_path_in_zip)[1]
                preview_filename = f"{uuid.uuid4()}{preview_ext}"
                preview_path = os.path.join(settings.storage_root, "previews", preview_filename)
                # Извлекаем файл из архива
                import zipfile
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    with zf.open(preview_path_in_zip) as src, open(preview_path, 'wb') as dst:
                        dst.write(src.read())
                # Сохраняем относительный путь
                preview_path = os.path.join("previews", preview_filename)

            # 4. Находим или создаём автора
            authors = await self.author_repo.list(name=author_name)
            if not authors:
                author = await self.author_repo.create(
                    AuthorCreate(name=author_name, email=author_email).model_dump()
                )
            else:
                author = authors[0]
                # Если email не задан, но автор уже есть, можно обновить
                if author_email and not author.email:
                    await self.author_repo.update(author.id, {"email": author_email})

            # 5. Создаём запись работы
            work_data = {
                "external_id": external_id,
                "author_id": author.id,
                "name": name or "Untitled",
                "description": description or "",
                "preview_path": preview_path,
                "zip_path": zip_path,
                "metadata": metadata,
            }
            work = await self.work_repo.create(work_data)
            return work

        except Exception as e:
            # Если ошибка, удаляем zip
            if os.path.exists(zip_path):
                os.remove(zip_path)
            raise HTTPException(status_code=400, detail=f"Failed to ingest work: {str(e)}")

    async def get_work(self, work_id: str) -> Work:
        work = await self.work_repo.get(work_id)
        if not work:
            raise HTTPException(status_code=404, detail="Work not found")
        return work

    async def list_works(self, author_id: Optional[str] = None) -> List[Work]:
        filters = {}
        if author_id:
            filters['author_id'] = author_id
        return await self.work_repo.list(**filters)

    async def delete_work(self, work_id: str) -> bool:
        # Проверяем, не используется ли работа в событиях/коллекциях
        # (пока не реализовано, позже добавим проверку)
        work = await self.work_repo.get(work_id)
        if not work:
            return False
        # Удаляем zip и preview
        if os.path.exists(work.zip_path):
            os.remove(work.zip_path)
        if work.preview_path:
            full_preview = os.path.join(settings.storage_root, work.preview_path)
            if os.path.exists(full_preview):
                os.remove(full_preview)
        # Удаляем из репозитория
        return await self.work_repo.delete(work_id)

    # Вспомогательная функция для чтения метаданных из пути
    async def read_zip_metadata_from_path(zip_path: str):
        # Используем ранее написанную функцию, но адаптируем под путь
        # Можно переиспользовать логику из zip_reader, но нужно передавать путь
        # Сделаем отдельную функцию в zip_reader
        from app.utils.zip_reader import read_zip_metadata_from_file_path
        return await read_zip_metadata_from_file_path(zip_path)