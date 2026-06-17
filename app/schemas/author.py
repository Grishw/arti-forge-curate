from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AuthorBase(BaseModel):
    external_id: Optional[str] = None
    name: str
    email: Optional[str] = None

class AuthorCreate(AuthorBase):
    pass

class Author(AuthorBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True