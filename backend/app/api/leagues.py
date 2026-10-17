from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import leagues as leagues_service

router = APIRouter()


@router.post("/leagues", status_code=201)
async def create_league(body: dict, db: AsyncSession = Depends(get_db)):
    return await leagues_service.create_league(db, body)
