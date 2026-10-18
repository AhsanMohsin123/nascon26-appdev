from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import moderation as moderation_service

router = APIRouter()


@router.post("/moderation/test")
async def moderation_test(body: dict, db: AsyncSession = Depends(get_db)):
    return await moderation_service.run_moderation_test(db, body)
