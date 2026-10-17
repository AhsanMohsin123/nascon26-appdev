from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import seed as seed_service

router = APIRouter()


@router.post("/reset")
async def reset(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        body = await request.json()
    except Exception:
        body = {}
    seed_val = body.get("seed", 42) if body else 42
    stock = body.get("stock", {"var-jersey-001-M": 1, "var-jersey-001-L": 5}) if body else {"var-jersey-001-M": 1, "var-jersey-001-L": 5}
    await seed_service.reset_and_seed(db, seed_val, stock)
    return {
        "status": "reset_complete",
        "seed": seed_val,
        "sports": ["football", "basketball", "cricket", "esports"],
        "tenants": ["tenant-alpha", "tenant-beta"],
        "stock": stock,
    }
