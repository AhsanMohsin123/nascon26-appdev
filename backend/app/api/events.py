from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import scoring as scoring_service

router = APIRouter()


@router.post("/events")
async def append_event(body: dict, db: AsyncSession = Depends(get_db)):
    return await scoring_service.append_event(db, body)


@router.get("/score/{match_id}")
async def get_score(match_id: str, db: AsyncSession = Depends(get_db)):
    return await scoring_service.get_score(db, match_id)
