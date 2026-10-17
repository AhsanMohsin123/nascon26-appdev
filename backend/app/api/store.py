from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import store as store_service

router = APIRouter()


@router.post("/checkout")
async def checkout(body: dict, db: AsyncSession = Depends(get_db)):
    return await store_service.checkout(db, body)


@router.get("/inventory/{variant_id}")
async def inventory(variant_id: str, db: AsyncSession = Depends(get_db)):
    return await store_service.get_inventory(db, variant_id)
