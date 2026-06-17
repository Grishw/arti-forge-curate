from app.repositories.json_repository import JsonRepository
from app.schemas.work import Work

class WorkRepository(JsonRepository[Work]):
    def __init__(self):
        super().__init__("works.json", Work)