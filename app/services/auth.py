from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, User
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token

class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()

    async def register(self, user_data: UserCreate) -> User:
        # Проверяем, существует ли пользователь с таким email
        existing = await self.user_repo.list(email=user_data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        # Хешируем пароль
        hashed = get_password_hash(user_data.password)
        user_dict = user_data.model_dump()
        user_dict.pop('password')
        user_dict['hashed_password'] = hashed
        user_dict['role'] = user_data.role or "curator"
        # Создаём пользователя
        new_user = await self.user_repo.create(user_dict)
        return new_user

    async def login(self, email: str, password: str) -> str:
        users = await self.user_repo.list(email=email)
        if not users:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        user = users[0]
        if not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        # Создаём JWT
        access_token = create_access_token(
            data={"sub": user.id, "role": user.role}
        )
        return access_token

    async def get_current_user(self, token: str) -> User:
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await self.user_repo.get(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user