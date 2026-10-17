from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import standings as standings_service

router = APIRouter()


@router.get("/standings/{league_id}")
async def get_standings(league_id: str, db: AsyncSession = Depends(get_db)):
    return await standings_service.compute_standings(db, league_id)
