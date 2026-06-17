from fastapi import APIRouter, HTTPException, Depends
from app.schemas.user import UserCreate, User
from app.services.auth import AuthService
from app.core.dependencies import get_current_user

router = APIRouter()

@router.post("/register", response_model=User)
async def register(user_data: UserCreate):
    auth_service = AuthService()
    return await auth_service.register(user_data)

@router.post("/login")
async def login(email: str, password: str):
    auth_service = AuthService()
    token = await auth_service.login(email, password)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user