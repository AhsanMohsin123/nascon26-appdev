"""Roster, transfers, loans and history."""
import json
from datetime import date, datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def setup(db: AsyncSession, body: dict) -> dict:
    league = body.get("league", {})
    squads = body.get("squads", [])
    players = body.get("players", [])
    matches_in_progress = body.get("matches_in_progress", [])

    league_id = league.get("league_id")
    sport_id = league.get("sport_id", "football")
    tenant_id = league.get("tenant_id", "tenant-alpha")

    await db.execute(text("DELETE FROM player_registrations WHERE league_id = :lid"), {"lid": league_id})
    await db.execute(text("DELETE FROM roster_audit WHERE league_id = :lid"), {"lid": league_id})

    league_config = json.dumps(league)
    await db.execute(text(
        "INSERT INTO leagues (id, tenant_id, sport_id, config) VALUES (:id, :tid, :sid, :cfg) "
        "ON CONFLICT (id) DO UPDATE SET config = :cfg"
    ), {"id": league_id, "tid": tenant_id, "sid": sport_id, "cfg": league_config})

    for sq in squads:
        await db.execute(text(
            "INSERT INTO squads (id, league_id, club_id, tenant_id, name) VALUES (:id, :lid, :cid, :tid, :name) ON CONFLICT DO NOTHING"
        ), {"id": sq["squad_id"], "lid": league_id, "cid": sq.get("club_id"), "tid": sq.get("tenant_id", tenant_id), "name": sq.get("name", "")})

    for mp in matches_in_progress:
        await db.execute(text(
            "INSERT INTO matches (id, league_id, sport_id, home_team_id, away_team_id, status) VALUES (:id, :lid, :sid, :home, :away, 'in_progress') ON CONFLICT DO NOTHING"
        ), {"id": mp["match_id"], "lid": league_id, "sid": sport_id, "home": mp.get("home_squad_id"), "away": mp.get("away_squad_id")})

    squad_counts = {sq["squad_id"]: 0 for sq in squads}
    for p in players:
        await db.execute(text(
            "INSERT INTO players (id, club_id, name, position) VALUES (:id, :cid, :name, :pos) ON CONFLICT DO NOTHING"
        ), {"id": p["player_id"], "cid": None, "name": p.get("name", p["player_id"]), "pos": p.get("position", "")})
        await db.execute(text(
            "INSERT INTO player_registrations (player_id, league_id, squad_id, role, registration_type, start_date) "
            "VALUES (:pid, :lid, :sid, :role, 'initial', CURRENT_DATE) ON CONFLICT DO NOTHING"
        ), {"pid": p["player_id"], "lid": league_id, "sid": p.get("squad_id"), "role": p.get("role", "substitute")})
        sq_id = p.get("squad_id")
        if sq_id in squad_counts:
            squad_counts[sq_id] += 1

    await db.commit()
    return {"league_id": league_id, "status": "configured", "squad_counts": squad_counts}


async def transfer(db: AsyncSession, body: dict) -> dict:
    req_id = body.get("request_id")
    league_id = body.get("league_id")
    player_id = body.get("player_id")
    transfer_type = body.get("type")
    from_squad = body.get("from_squad_id")
    to_squad = body.get("to_squad_id")
    effective_date = body.get("effective_date")
    reason = body.get("reason", "")
    requested_by = body.get("requested_by", "unknown")

    existing = await db.execute(text("SELECT id FROM roster_audit WHERE id = :id"), {"id": req_id})
    if existing.fetchone():
        row = await db.execute(text("SELECT response FROM roster_audit WHERE id = :id"), {"id": req_id})
        r = row.fetchone()
        return json.loads(r[0]) if r and r[0] else {}

    player_row = await db.execute(text("SELECT id FROM players WHERE id = :id"), {"id": player_id})
    if not player_row.fetchone():
        raise HTTPException(404, {"error": {"code": "PLAYER_NOT_FOUND", "message": f"Player {player_id} not found.", "details": {}}})

    reg_row = await db.execute(text(
        "SELECT squad_id, role, registration_type, loan_end_date FROM player_registrations WHERE player_id = :pid AND league_id = :lid"
    ), {"pid": player_id, "lid": league_id})
    reg = reg_row.fetchone()

    if not reg or reg[0] != from_squad:
        raise HTTPException(409, {"error": {"code": "NOT_IN_SQUAD", "message": f"Player {player_id} is not in squad {from_squad}.", "details": {}}})

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    audit_id = f"au-{req_id}"
    response = {
        "request_id": req_id,
        "status": "accepted",
        "state": "active",
        "blocking_match_id": None,
        "registration": {
            "player_id": player_id,
            "league_id": league_id,
            "squad_id": to_squad,
            "parent_squad_id": None,
            "registration_type": transfer_type,
            "start_date": effective_date,
            "loan_end_date": body.get("loan_end_date"),
            "role": "substitute",
        },
        "audit_entry": {
            "audit_id": audit_id,
            "action": transfer_type,
            "player_id": player_id,
            "league_id": league_id,
            "from_squad_id": from_squad,
            "to_squad_id": to_squad,
            "effective_date": effective_date,
            "state": "active",
            "who": requested_by,
            "when": now,
            "why": reason,
        },
    }

    await db.execute(text(
        "UPDATE player_registrations SET squad_id = :to_squad, role = 'substitute', registration_type = :rtype, start_date = :edate, loan_end_date = :lend "
        "WHERE player_id = :pid AND league_id = :lid"
    ), {"to_squad": to_squad, "rtype": transfer_type, "edate": effective_date, "lend": body.get("loan_end_date"), "pid": player_id, "lid": league_id})

    await db.execute(text(
        "INSERT INTO roster_audit (id, league_id, player_id, action, from_squad, to_squad, effective_date, who, why, when_, response) "
        "VALUES (:id, :lid, :pid, :action, :from_sq, :to_sq, :edate, :who, :why, :when_, :response)"
    ), {"id": req_id, "lid": league_id, "pid": player_id, "action": transfer_type,
        "from_sq": from_squad, "to_sq": to_squad, "edate": effective_date,
        "who": requested_by, "why": reason, "when_": now, "response": json.dumps(response)})

    await db.commit()
    return response


async def history(db: AsyncSession, player_id: str, as_of: str = None) -> dict:
    player_row = await db.execute(text("SELECT id FROM players WHERE id = :id"), {"id": player_id})
    if not player_row.fetchone():
        raise HTTPException(404, {"error": {"code": "PLAYER_NOT_FOUND", "message": f"Player {player_id} not found.", "details": {}}})

    today = as_of or date.today().isoformat()

    reg_row = await db.execute(text(
        "SELECT squad_id, league_id FROM player_registrations WHERE player_id = :pid ORDER BY start_date DESC LIMIT 1"
    ), {"pid": player_id})
    reg = reg_row.fetchone()

    audit_rows = await db.execute(text(
        "SELECT id, action, from_squad, to_squad, effective_date, who, why, when_ FROM roster_audit WHERE player_id = :pid ORDER BY when_ ASC"
    ), {"pid": player_id})
    history_entries = []
    league_id = reg[1] if reg else None
    for row in audit_rows.fetchall():
        history_entries.append({
            "audit_id": row[0],
            "action": row[1],
            "player_id": player_id,
            "league_id": league_id,
            "from_squad_id": row[2],
            "to_squad_id": row[3],
            "effective_date": row[4],
            "who": row[5],
            "why": row[6],
            "when": row[7],
        })

    return {
        "player_id": player_id,
        "as_of": today,
        "league_id": league_id,
        "current_squad_id": reg[0] if reg else None,
        "parent_squad_id": None,
        "history": history_entries,
    }
