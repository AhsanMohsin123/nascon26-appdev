"""Sport taxonomy — data-driven, no hard-coded sport names."""
import json
import re
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


SPORT_ID_RE = re.compile(r"^[a-z0-9_-]{2,40}$")


async def create_sport(db: AsyncSession, body: dict) -> dict:
    sport_id = body.get("sport_id")
    if not sport_id or not SPORT_ID_RE.match(sport_id):
        raise HTTPException(400, {"error": {"code": "VALIDATION_ERROR", "message": "Invalid sport_id", "details": {"fields": ["sport_id"]}}})

    existing = await db.execute(text("SELECT id FROM sports WHERE id = :id"), {"id": sport_id})
    if existing.fetchone():
        raise HTTPException(409, {"error": {"code": "SPORT_EXISTS", "message": f"Sport {sport_id} already exists.", "details": {}}})

    name = body.get("name", "")
    if not name or len(name) > 80:
        raise HTTPException(400, {"error": {"code": "VALIDATION_ERROR", "message": "Invalid name", "details": {"fields": ["name"]}}})

    await db.execute(text(
        "INSERT INTO sports (id, name, config) VALUES (:id, :name, :config)"
    ), {"id": sport_id, "name": name, "config": json.dumps(body)})
    await db.commit()

    return {"sport_id": sport_id, "status": "created", "config": body}


async def get_sport(db: AsyncSession, sport_id: str) -> dict:
    row = await db.execute(text("SELECT config FROM sports WHERE id = :id"), {"id": sport_id})
    r = row.fetchone()
    if not r:
        raise HTTPException(404, {"error": {"code": "SPORT_NOT_FOUND", "message": f"Sport {sport_id} not found.", "details": {}}})
    return json.loads(r[0])
