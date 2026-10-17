from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import offline_sync as sync_service

router = APIRouter()


@router.post("/offline-sync")
async def offline_sync(body: dict, db: AsyncSession = Depends(get_db)):
    return await sync_service.process(db, body)
