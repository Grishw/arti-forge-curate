from app.repositories.json_repository import JsonRepository
from app.schemas.user import User

class UserRepository(JsonRepository[User]):
    def __init__(self):
        super().__init__("users.json", User)