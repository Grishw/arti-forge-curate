from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.user import User
from app.services.auth import AuthService

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    auth_service = AuthService()
    user = await auth_service.get_current_user(credentials.credentials)
    return user

async def get_current_curator_or_admin(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["curator", "admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

async def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin rights required")
    return current_user