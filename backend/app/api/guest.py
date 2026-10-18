from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import guest_cart as guest_cart_service

router = APIRouter()


@router.post("/guest/cart-merge")
async def cart_merge(body: dict, db: AsyncSession = Depends(get_db)):
    return await guest_cart_service.merge_guest_cart(db, body)
