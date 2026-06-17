from app.repositories.json_repository import JsonRepository
from app.schemas.event import Event

class EventRepository(JsonRepository[Event]):
    def __init__(self):
        super().__init__("events.json", Event)