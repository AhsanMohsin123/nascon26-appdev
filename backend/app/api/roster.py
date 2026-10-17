from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import roster as roster_service

router = APIRouter()


@router.post("/roster/setup", status_code=201)
async def setup_roster(body: dict, db: AsyncSession = Depends(get_db)):
    return await roster_service.setup(db, body)


@router.post("/roster/transfer")
async def transfer(body: dict, db: AsyncSession = Depends(get_db)):
    return await roster_service.transfer(db, body)


@router.get("/roster/history/{player_id}")
async def roster_history(player_id: str, as_of: str = Query(None), db: AsyncSession = Depends(get_db)):
    return await roster_service.history(db, player_id, as_of)
