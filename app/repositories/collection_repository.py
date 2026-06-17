from app.repositories.json_repository import JsonRepository
from app.schemas.collection import Collection

class CollectionRepository(JsonRepository[Collection]):
    def __init__(self):
        super().__init__("collections.json", Collection)