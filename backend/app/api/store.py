from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import store as store_service
from app.auth.middleware import reject_guest_write

router = APIRouter()


@router.post("/checkout")
async def checkout(body: dict, request: Request, db: AsyncSession = Depends(get_db)):
    reject_guest_write(request)
    return await store_service.checkout(db, body)


@router.get("/inventory/{variant_id}")
async def inventory(variant_id: str, db: AsyncSession = Depends(get_db)):
    return await store_service.get_inventory(db, variant_id)
