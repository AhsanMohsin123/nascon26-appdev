from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import streaming as streaming_service

router = APIRouter()


@router.post("/stream/key")
async def stream_key(body: dict, db: AsyncSession = Depends(get_db)):
    status_code, response = await streaming_service.manage_stream_key(db, body)
    return JSONResponse(status_code=status_code, content=response)
