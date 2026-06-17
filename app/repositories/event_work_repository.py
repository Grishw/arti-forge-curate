from app.repositories.json_repository import JsonRepository
from app.schemas.event_work import EventWork

class EventWorkRepository(JsonRepository[EventWork]):
    def __init__(self):
        super().__init__("event_works.json", EventWork)