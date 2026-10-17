from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import sports as sports_service

router = APIRouter()


@router.post("/sports", status_code=201)
async def create_sport(body: dict, db: AsyncSession = Depends(get_db)):
    return await sports_service.create_sport(db, body)
