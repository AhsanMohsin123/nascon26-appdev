from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domain import rbac as rbac_service
from app.auth.middleware import require_auth

router = APIRouter()


@router.post("/rbac-matrix")
async def rbac_matrix(db: AsyncSession = Depends(get_db)):
    return await rbac_service.get_matrix(db)


@router.post("/rbac/tenants")
async def probe_tenants(request: Request, db: AsyncSession = Depends(get_db)):
    return await rbac_service.probe(request, db, "create_tenant", None)


@router.post("/rbac/leagues/{league_id}/fixtures")
async def probe_league_fixtures(league_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await rbac_service.probe(request, db, "manage_fixtures", {"league_id": league_id})


@router.post("/rbac/clubs/{club_id}/roster")
async def probe_club_roster(club_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await rbac_service.probe(request, db, "manage_roster", {"club_id": club_id})


@router.post("/rbac/clubs/{club_id}/products")
async def probe_club_products(club_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await rbac_service.probe(request, db, "manage_products", {"club_id": club_id})


@router.patch("/rbac/players/{player_id}")
async def probe_player(player_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await rbac_service.probe(request, db, "update_player", {"player_id": player_id})


@router.get("/rbac/clubs/{club_id}")
async def probe_view_club(club_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await rbac_service.probe(request, db, "view_club", {"club_id": club_id})


@router.get("/rbac/platform/config")
async def probe_platform_config(request: Request, db: AsyncSession = Depends(get_db)):
    return await rbac_service.probe(request, db, "platform_config", None)
