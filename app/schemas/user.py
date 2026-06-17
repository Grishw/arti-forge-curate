from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "curator"  # "curator" или "admin"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None

class User(UserBase):
    id: str
    hashed_password: str
    created_at: datetime

    class Config:
        from_attributes = True