from app.repositories.json_repository import JsonRepository
from app.schemas.analytics import Analytics

class AnalyticsRepository(JsonRepository[Analytics]):
    def __init__(self):
        super().__init__("analytics.json", Analytics)