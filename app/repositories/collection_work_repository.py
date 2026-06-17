from app.repositories.json_repository import JsonRepository
from app.schemas.collection_work import CollectionWork

class CollectionWorkRepository(JsonRepository[CollectionWork]):
    def __init__(self):
        super().__init__("collection_works.json", CollectionWork)