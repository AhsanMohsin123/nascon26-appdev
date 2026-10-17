"""5-tier RBAC — Super Admin, League Organizer, Club Manager, Player, Viewer."""
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.auth.jwt import create_access_token, decode_token
from jose import JWTError
from datetime import timedelta


ROLE_ORDER = ["super_admin", "league_organizer", "club_manager", "player", "viewer"]

PERMISSION_MATRIX = {
    "create_tenant":  {"super_admin"},
    "manage_fixtures": {"super_admin", "league_organizer"},
    "manage_roster":  {"super_admin", "club_manager"},
    "manage_products": {"super_admin", "club_manager"},
    "update_player":  {"super_admin", "club_manager", "player"},
    "view_club":      {"super_admin", "league_organizer", "club_manager", "player", "viewer"},
    "platform_config": {"super_admin"},
}


def _make_token(role: str, tenant_id: str, league_id=None, club_id=None, player_id=None) -> str:
    data = {"sub": f"{role}@nascon.test", "role": role, "tenant_id": tenant_id}
    if league_id:
        data["league_id"] = league_id
    if club_id:
        data["club_id"] = club_id
    if player_id:
        data["player_id"] = player_id
    return create_access_token(data, expires_delta=timedelta(hours=2))


async def get_matrix(db: AsyncSession) -> dict:
    return {
        "tokens": {
            "super_admin": _make_token("super_admin", "tenant-alpha"),
            "league_organizer": _make_token("league_organizer", "tenant-alpha", league_id="league-alpha-1"),
            "club_manager": _make_token("club_manager", "tenant-alpha", club_id="club-alpha-1"),
            "player": _make_token("player", "tenant-alpha", club_id="club-alpha-1", player_id="player-alpha-1"),
            "viewer": _make_token("viewer", "tenant-alpha"),
        },
        "context": {
            "tenant_id": "tenant-alpha",
            "foreign_tenant_id": "tenant-beta",
            "own_league_id": "league-alpha-1",
            "other_league_id": "league-alpha-2",
            "foreign_league_id": "league-beta-1",
            "own_club_id": "club-alpha-1",
            "other_club_id": "club-alpha-2",
            "foreign_club_id": "club-beta-1",
            "own_player_id": "player-alpha-1",
            "other_player_id": "player-alpha-2",
            "foreign_player_id": "player-beta-1",
        },
    }


async def probe(request: Request, db: AsyncSession, permission: str, context: dict) -> dict:
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, {"error": {"code": "UNAUTHENTICATED", "message": "Missing or invalid token.", "details": {}}})

    token = auth[7:]
    try:
        claims = decode_token(token)
    except JWTError:
        raise HTTPException(401, {"error": {"code": "UNAUTHENTICATED", "message": "Invalid or expired token.", "details": {}}})

    role = claims.get("role", "viewer")
    token_tenant = claims.get("tenant_id")
    token_league = claims.get("league_id")
    token_club = claims.get("club_id")
    token_player = claims.get("player_id")

    allowed_roles = PERMISSION_MATRIX.get(permission, set())

    if role == "super_admin":
        return {"authorized": True}

    if role not in allowed_roles:
        raise HTTPException(403, {"error": {"code": "FORBIDDEN", "message": "Access denied.", "details": {}}})

    if context:
        # Tenant isolation
        req_tenant = None
        if "league_id" in context:
            lid = context["league_id"]
            row = await db.execute(text("SELECT tenant_id FROM leagues WHERE id = :id"), {"id": lid})
            r = row.fetchone()
            if r:
                req_tenant = r[0]
        elif "club_id" in context:
            cid = context["club_id"]
            row = await db.execute(text("SELECT tenant_id FROM clubs WHERE id = :id"), {"id": cid})
            r = row.fetchone()
            if r:
                req_tenant = r[0]

        if req_tenant and req_tenant != token_tenant:
            raise HTTPException(403, {"error": {"code": "FORBIDDEN", "message": "Cross-tenant access denied.", "details": {}}})

        if role == "league_organizer" and "league_id" in context:
            if token_league != context["league_id"]:
                raise HTTPException(403, {"error": {"code": "FORBIDDEN", "message": "Access denied to this league.", "details": {}}})

        if role == "club_manager" and "club_id" in context:
            if token_club != context["club_id"]:
                raise HTTPException(403, {"error": {"code": "FORBIDDEN", "message": "Access denied to this club.", "details": {}}})

        if role == "player" and "player_id" in context:
            if token_player != context["player_id"]:
                raise HTTPException(403, {"error": {"code": "FORBIDDEN", "message": "Access denied.", "details": {}}})

    return {"authorized": True}
