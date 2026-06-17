import os
import json
import uuid
from typing import List, Optional, Dict, Any, Type, TypeVar, Generic
from datetime import datetime
import aiofiles
from pydantic import BaseModel
from app.core.config import settings

T = TypeVar('T', bound=BaseModel)

class JsonRepository(Generic[T]):
    def __init__(self, filename: str, model_class: Type[T]):
        self.filename = os.path.join(settings.data_root, filename)
        self.model_class = model_class

    async def _read_all(self) -> List[Dict[str, Any]]:
        """Асинхронно читает весь JSON-файл."""
        if not os.path.exists(self.filename):
            return []
        async with aiofiles.open(self.filename, 'r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content) if content else []

    async def _write_all(self, data: List[Dict[str, Any]]) -> None:
        """Асинхронно перезаписывает JSON-файл."""
        async with aiofiles.open(self.filename, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2, default=str))

    async def list(self, **filters) -> List[T]:
        """Фильтрация по полям (точное совпадение)."""
        items = await self._read_all()
        for key, value in filters.items():
            items = [item for item in items if item.get(key) == value]
        return [self.model_class(**item) for item in items]

    async def get(self, id: str) -> Optional[T]:
        items = await self._read_all()
        for item in items:
            if item.get('id') == id:
                return self.model_class(**item)
        return None

    async def create(self, data: Dict[str, Any]) -> T:
        items = await self._read_all()
        # Добавляем id и created_at, если их нет
        if 'id' not in data or not data['id']:
            data['id'] = str(uuid.uuid4())
        if 'created_at' not in data:
            data['created_at'] = datetime.utcnow().isoformat()
        # Валидируем через модель (опционально)
        model_instance = self.model_class(**data)
        items.append(model_instance.model_dump())
        await self._write_all(items)
        return model_instance

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        items = await self._read_all()
        for i, item in enumerate(items):
            if item.get('id') == id:
                # Обновляем только переданные поля
                item.update(data)
                # Валидируем
                model_instance = self.model_class(**item)
                items[i] = model_instance.model_dump()
                await self._write_all(items)
                return model_instance
        return None

    async def delete(self, id: str) -> bool:
        items = await self._read_all()
        for i, item in enumerate(items):
            if item.get('id') == id:
                items.pop(i)
                await self._write_all(items)
                return True
        return False