from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import fixtures as fixtures_service

router = APIRouter()


@router.post("/fixtures")
async def generate_fixtures(body: dict, db: AsyncSession = Depends(get_db)):
    return await fixtures_service.generate(db, body)
