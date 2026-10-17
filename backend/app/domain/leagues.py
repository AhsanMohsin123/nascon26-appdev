"""League registration and management."""
import json
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def create_league(db: AsyncSession, body: dict) -> dict:
    league_id = body.get("league_id")
    sport_id = body.get("sport_id")
    teams = body.get("teams", [])
    fixtures = body.get("fixtures", [])

    if not league_id or not sport_id or not teams or not fixtures:
        raise HTTPException(400, {"error": {"code": "VALIDATION_ERROR", "message": "Missing required fields", "details": {"fields": []}}})

    sport_row = await db.execute(text("SELECT id FROM sports WHERE id = :id"), {"id": sport_id})
    if not sport_row.fetchone():
        raise HTTPException(404, {"error": {"code": "SPORT_NOT_FOUND", "message": f"Sport {sport_id} not found.", "details": {}}})

    existing = await db.execute(text("SELECT id FROM leagues WHERE id = :id"), {"id": league_id})
    if existing.fetchone():
        raise HTTPException(409, {"error": {"code": "LEAGUE_EXISTS", "message": f"League {league_id} already exists.", "details": {}}})

    await db.execute(text(
        "INSERT INTO leagues (id, sport_id, config) VALUES (:id, :sport_id, :config)"
    ), {"id": league_id, "sport_id": sport_id, "config": json.dumps(body)})

    for team_id in teams:
        await db.execute(text(
            "INSERT INTO league_teams (league_id, team_id) VALUES (:league_id, :team_id) ON CONFLICT DO NOTHING"
        ), {"league_id": league_id, "team_id": team_id})

    for fixture in fixtures:
        match_id = fixture["match_id"]
        existing_match = await db.execute(text("SELECT id FROM matches WHERE id = :id"), {"id": match_id})
        if existing_match.fetchone():
            raise HTTPException(409, {"error": {"code": "MATCH_EXISTS", "message": f"Match {match_id} already exists.", "details": {}}})
        await db.execute(text(
            "INSERT INTO matches (id, league_id, sport_id, home_team_id, away_team_id, status) "
            "VALUES (:id, :league_id, :sport_id, :home, :away, 'upcoming')"
        ), {"id": match_id, "league_id": league_id, "sport_id": sport_id, "home": fixture["home"], "away": fixture["away"]})

    await db.commit()

    return {"league_id": league_id, "status": "created", "team_count": len(teams), "fixture_count": len(fixtures)}
