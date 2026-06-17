from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from typing import Optional
from app.schemas.user import User
from app.services.work_service import WorkService
from app.schemas.work import Work
from app.core.dependencies import get_current_curator_or_admin, get_current_user
from app.core.config import settings

router = APIRouter()

@router.post("/ingest", response_model=Work)
async def ingest_work(
    file: UploadFile = File(...),
    external_id: str = Form(...),
    author_name: str = Form(...),
    author_email: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    # Простая защита API-ключом (пока без депенденси, чтобы не требовать JWT для Forge)
    api_key: str = Query(...),
):
    if api_key != settings.forge_ingest_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    service = WorkService()
    return await service.ingest_work(
        file=file,
        external_id=external_id,
        author_name=author_name,
        author_email=author_email,
        name=name,
        description=description,
    )

@router.get("/", response_model=list[Work])
async def list_works(
    author_id: Optional[str] = None,
    current_user: User = Depends(get_current_curator_or_admin),
):
    service = WorkService()
    filters = {}
    if author_id:
        filters["author_id"] = author_id
    return await service.list_works(**filters)

@router.get("/{work_id}", response_model=Work)
async def get_work(
    work_id: str,
    current_user: User = Depends(get_current_curator_or_admin),
):
    service = WorkService()
    work = await service.get_work(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    return work

@router.delete("/{work_id}")
async def delete_work(
    work_id: str,
    current_user: User = Depends(get_current_curator_or_admin),
):
    service = WorkService()
    deleted = await service.delete_work(work_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Work not found")
    return {"status": "deleted"}