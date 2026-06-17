from app.repositories.json_repository import JsonRepository
from app.schemas.author import Author

class AuthorRepository(JsonRepository[Author]):
    def __init__(self):
        super().__init__("authors.json", Author)