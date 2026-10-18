from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import observability as observability_service

router = APIRouter()
audit_router = APIRouter()


@router.get("/metrics")
async def metrics(db: AsyncSession = Depends(get_db)):
    body = await observability_service.render_metrics(db)
    return PlainTextResponse(content=body, media_type="text/plain; version=0.0.4")


@audit_router.delete("/privacy/user/{user_id}")
async def erase_user(user_id: str, db: AsyncSession = Depends(get_db)):
    return await observability_service.erase_user(db, user_id)
