from fastapi import APIRouter
from app.api.v1.endpoints import auth, works, events, collections

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(works.router, prefix="/works", tags=["works"])
router.include_router(events.router, prefix="/events", tags=["events"])
router.include_router(collections.router, prefix="/collections", tags=["collections"])