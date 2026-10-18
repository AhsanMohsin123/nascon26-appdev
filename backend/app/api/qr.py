from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import qr as qr_service

router = APIRouter()
public_router = APIRouter()


@router.get("/qr/{entity_id}")
async def get_qr(entity_id: str, request: Request, inspect: bool = False, db: AsyncSession = Depends(get_db)):
    return await qr_service.get_qr_metadata(db, entity_id, inspect=inspect, user_agent=request.headers.get("user-agent"))


@router.get("/qr/{entity_id}/export.svg")
async def export_svg(entity_id: str, db: AsyncSession = Depends(get_db)):
    svg = await qr_service.export_svg(db, entity_id)
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/qr/{entity_id}/export.png")
async def export_png(entity_id: str, db: AsyncSession = Depends(get_db)):
    png_bytes = await qr_service.export_png(db, entity_id)
    return Response(content=png_bytes, media_type="image/png")


@router.get("/qr/{entity_id}/export.pdf")
async def export_pdf(entity_id: str, db: AsyncSession = Depends(get_db)):
    pdf_bytes = await qr_service.export_pdf(db, entity_id)
    return Response(content=pdf_bytes, media_type="application/pdf")


@public_router.get("/q/{short_code}")
async def resolve_short_code(short_code: str, request: Request, db: AsyncSession = Depends(get_db)):
    target_route = await qr_service.resolve_short_code(db, short_code, user_agent=request.headers.get("user-agent"))
    return RedirectResponse(url=target_route, status_code=302)
