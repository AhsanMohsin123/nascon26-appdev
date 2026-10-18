from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import costream as costream_service

router = APIRouter()


@router.post("/costream/session")
async def costream_session(body: dict, db: AsyncSession = Depends(get_db)):
    status_code, response = await costream_service.manage_session(db, body)
    return JSONResponse(status_code=status_code, content=response)
