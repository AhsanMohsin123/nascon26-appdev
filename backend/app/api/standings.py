from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.domain import standings as standings_service
from app.domain import scoring as scoring_service

router = APIRouter()


@router.get("/standings/{league_id}")
async def get_standings(league_id: str, db: AsyncSession = Depends(get_db)):
    return await standings_service.compute_standings(db, league_id)


@router.get("/matches/{league_id}")
async def list_matches(league_id: str, db: AsyncSession = Depends(get_db)):
    rows = await db.execute(text("SELECT id FROM matches WHERE league_id=:lid ORDER BY id"), {"lid": league_id})
    out = []
    for r in rows.fetchall():
        try:
            out.append(await scoring_service.get_score(db, r[0]))
        except Exception:
            pass
    return {"league_id": league_id, "matches": out}
