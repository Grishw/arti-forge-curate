from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TypeVar, Generic

T = TypeVar('T')

class Repository(ABC, Generic[T]):
    @abstractmethod
    async def list(self, **filters) -> List[T]:
        """Получить все записи, возможно с фильтрацией."""
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """Получить запись по id."""
        pass

    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> T:
        """Создать новую запись."""
        pass

    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """Обновить запись."""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Удалить запись."""
        pass