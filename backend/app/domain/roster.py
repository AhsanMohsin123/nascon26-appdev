"""Roster operations — all 8 rule checks in exact order, immutable audit trail."""
import json
from datetime import date, datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def setup(db: AsyncSession, body: dict) -> dict:
    league_cfg = body.get("league", {})
    squads = body.get("squads", [])
    players = body.get("players", [])
    matches_in_progress = body.get("matches_in_progress", [])

    league_id = league_cfg.get("league_id")
    sport_id = league_cfg.get("sport_id", "football")
    tenant_id = league_cfg.get("tenant_id", "tenant-alpha")

    # Clear existing roster state for this league
    await db.execute(text("DELETE FROM roster_audit WHERE league_id=:lid"), {"lid": league_id})
    await db.execute(text("DELETE FROM player_registrations WHERE league_id=:lid"), {"lid": league_id})

    # Upsert league
    await db.execute(text(
        "INSERT INTO leagues (id, tenant_id, sport_id, config) VALUES (:id, :tid, :sid, :cfg) "
        "ON CONFLICT (id) DO UPDATE SET config=:cfg, tenant_id=:tid"
    ), {"id": league_id, "tid": tenant_id, "sid": sport_id, "cfg": json.dumps(league_cfg)})

    # Upsert squads
    for sq in squads:
        await db.execute(text(
            "INSERT INTO squads (id, league_id, club_id, tenant_id, name) VALUES (:id,:lid,:cid,:tid,:name) "
            "ON CONFLICT (id) DO UPDATE SET league_id=:lid"
        ), {"id": sq["squad_id"], "lid": league_id, "cid": sq.get("club_id"), "tid": sq.get("tenant_id", tenant_id), "name": sq.get("name", "")})

    # Seed matches in progress
    for mp in matches_in_progress:
        await db.execute(text(
            "INSERT INTO matches (id,league_id,sport_id,home_team_id,away_team_id,status) "
            "VALUES (:id,:lid,:sid,:home,:away,'in_progress') ON CONFLICT (id) DO UPDATE SET status='in_progress'"
        ), {"id": mp["match_id"], "lid": league_id, "sid": sport_id, "home": mp.get("home_squad_id"), "away": mp.get("away_squad_id")})

    # Upsert players + registrations
    squad_counts = {sq["squad_id"]: 0 for sq in squads}
    for p in players:
        await db.execute(text(
            "INSERT INTO players (id,club_id,name,position) VALUES (:id,:cid,:name,:pos) ON CONFLICT (id) DO NOTHING"
        ), {"id": p["player_id"], "cid": None, "name": p.get("name", p["player_id"]), "pos": p.get("position", "")})
        await db.execute(text(
            "INSERT INTO player_registrations (player_id,league_id,squad_id,role,registration_type,start_date) "
            "VALUES (:pid,:lid,:sid,:role,'initial',CURRENT_DATE) ON CONFLICT (player_id,league_id) DO UPDATE SET squad_id=:sid"
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
    effective_date_str = body.get("effective_date")
    loan_end_str = body.get("loan_end_date")
    reason = body.get("reason", "")
    requested_by = body.get("requested_by", "unknown")

    # Idempotency
    existing = await db.execute(text("SELECT response FROM roster_audit WHERE id=:id"), {"id": req_id})
    row = existing.fetchone()
    if row:
        return json.loads(row[0])

    # Rule 1: Schema validation
    if not req_id or not league_id or not player_id or not transfer_type or not from_squad or not effective_date_str:
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Missing required fields.", "details": {"fields": []}}})
    if transfer_type == "loan" and not loan_end_str:
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "loan_end_date required for loan.", "details": {"fields": ["loan_end_date"]}}})
    if transfer_type != "release" and not to_squad:
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "to_squad_id required.", "details": {"fields": ["to_squad_id"]}}})
    if transfer_type == "loan" and loan_end_str and loan_end_str <= effective_date_str:
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "loan_end_date must be after effective_date.", "details": {"fields": ["loan_end_date"]}}})

    # Rule 2: Existence checks
    league_row = await db.execute(text("SELECT config, tenant_id FROM leagues WHERE id=:id"), {"id": league_id})
    league = league_row.fetchone()
    if not league:
        raise HTTPException(404, detail={"error": {"code": "LEAGUE_NOT_FOUND", "message": f"League {league_id} not found.", "details": {}}})
    league_cfg = json.loads(league[0]) if league[0] else {}
    league_tenant = league[1]

    player_row = await db.execute(text("SELECT id FROM players WHERE id=:id"), {"id": player_id})
    if not player_row.fetchone():
        raise HTTPException(404, detail={"error": {"code": "PLAYER_NOT_FOUND", "message": f"Player {player_id} not found.", "details": {}}})

    from_squad_row = await db.execute(text("SELECT tenant_id FROM squads WHERE id=:id"), {"id": from_squad})
    fsq = from_squad_row.fetchone()
    if not fsq:
        raise HTTPException(404, detail={"error": {"code": "SQUAD_NOT_FOUND", "message": f"Squad {from_squad} not found.", "details": {}}})

    if to_squad:
        to_squad_row = await db.execute(text("SELECT tenant_id FROM squads WHERE id=:id"), {"id": to_squad})
        tsq = to_squad_row.fetchone()
        if not tsq:
            raise HTTPException(404, detail={"error": {"code": "SQUAD_NOT_FOUND", "message": f"Squad {to_squad} not found.", "details": {}}})

    # Rule 3: Cross-tenant check
    if fsq[0] != league_tenant:
        raise HTTPException(409, detail={"error": {"code": "CROSS_TENANT_TRANSFER", "message": "Squads must belong to league's tenant.", "details": {}}})
    if to_squad and tsq[0] != league_tenant:
        raise HTTPException(409, detail={"error": {"code": "CROSS_TENANT_TRANSFER", "message": "Destination squad belongs to different tenant.", "details": {}}})

    # Rule 4: Player current squad
    reg_row = await db.execute(text(
        "SELECT squad_id, role, registration_type, loan_end_date FROM player_registrations WHERE player_id=:pid AND league_id=:lid"
    ), {"pid": player_id, "lid": league_id})
    reg = reg_row.fetchone()
    if not reg or reg[0] != from_squad:
        raise HTTPException(409, detail={"error": {"code": "NOT_IN_SQUAD", "message": f"Player {player_id} is not in squad {from_squad}.", "details": {}}})

    # Rule 5: Transfer window (transfers/loans only)
    if transfer_type in ("transfer", "loan"):
        window = league_cfg.get("transfer_window", {})
        window_open = window.get("open")
        window_close = window.get("close")
        if window_open and window_close:
            if not (window_open <= effective_date_str <= window_close):
                raise HTTPException(409, detail={"error": {"code": "TRANSFER_WINDOW_CLOSED", "message": "Transfer window is closed.", "details": {}}})

    # Rule 6: Player on loan
    if reg[2] == "loan" and reg[3] and reg[3] >= effective_date_str:
        raise HTTPException(409, detail={"error": {"code": "PLAYER_ON_LOAN", "message": f"Player {player_id} is currently on loan.", "details": {}}})

    # Rule 7: Destination squad size
    if transfer_type in ("transfer", "loan") and to_squad:
        max_sq = league_cfg.get("max_squad_size", 25)
        count_row = await db.execute(text(
            "SELECT COUNT(*) FROM player_registrations WHERE squad_id=:sid AND league_id=:lid"
        ), {"sid": to_squad, "lid": league_id})
        current_count = count_row.scalar() or 0
        if current_count + 1 > max_sq:
            raise HTTPException(409, detail={"error": {"code": "SQUAD_FULL", "message": f"Squad {to_squad} is full.", "details": {}}})

    # Rule 8: Min position requirement on source squad
    required_positions = league_cfg.get("required_positions", {})
    if required_positions:
        player_pos_row = await db.execute(text("SELECT position FROM players WHERE id=:id"), {"id": player_id})
        player_pos = player_pos_row.scalar()
        if player_pos and player_pos in required_positions:
            min_req = required_positions[player_pos]
            pos_count_row = await db.execute(text(
                "SELECT COUNT(*) FROM player_registrations pr JOIN players p ON pr.player_id=p.id "
                "WHERE pr.squad_id=:sid AND pr.league_id=:lid AND p.position=:pos"
            ), {"sid": from_squad, "lid": league_id, "pos": player_pos})
            pos_count = pos_count_row.scalar() or 0
            if pos_count - 1 < min_req:
                raise HTTPException(409, detail={"error": {"code": "MIN_POSITION_VIOLATION", "message": f"Cannot remove last {player_pos} from squad.", "details": {}}})

    # Check in-progress match
    in_progress_row = await db.execute(text(
        "SELECT id FROM matches WHERE status='in_progress' AND (home_team_id=:sq OR away_team_id=:sq)"
    ), {"sq": from_squad})
    live_match = in_progress_row.fetchone()
    state = "deferred_until_match_end" if live_match else "active"
    blocking_match = live_match[0] if live_match else None

    # Apply effect
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    audit_id = f"au-{req_id}"

    if transfer_type == "transfer":
        await db.execute(text(
            "UPDATE player_registrations SET squad_id=:to_sq, role='substitute', registration_type='transfer', start_date=:edate, loan_end_date=NULL "
            "WHERE player_id=:pid AND league_id=:lid"
        ), {"to_sq": to_squad, "edate": effective_date_str, "pid": player_id, "lid": league_id})
        reg_out = {
            "player_id": player_id, "league_id": league_id, "squad_id": to_squad,
            "parent_squad_id": None, "registration_type": "transfer",
            "start_date": effective_date_str, "loan_end_date": None, "role": "substitute"
        }
    elif transfer_type == "loan":
        await db.execute(text(
            "UPDATE player_registrations SET squad_id=:to_sq, role='substitute', registration_type='loan', "
            "start_date=:edate, loan_end_date=:lend, parent_squad_id=:from_sq "
            "WHERE player_id=:pid AND league_id=:lid"
        ), {"to_sq": to_squad, "edate": effective_date_str, "lend": loan_end_str, "from_sq": from_squad, "pid": player_id, "lid": league_id})
        reg_out = {
            "player_id": player_id, "league_id": league_id, "squad_id": to_squad,
            "parent_squad_id": from_squad, "registration_type": "loan",
            "start_date": effective_date_str, "loan_end_date": loan_end_str, "role": "substitute"
        }
    else:  # release
        await db.execute(text(
            "DELETE FROM player_registrations WHERE player_id=:pid AND league_id=:lid"
        ), {"pid": player_id, "lid": league_id})
        reg_out = None

    audit_entry = {
        "audit_id": audit_id, "action": transfer_type, "player_id": player_id,
        "league_id": league_id, "from_squad_id": from_squad, "to_squad_id": to_squad,
        "effective_date": effective_date_str, "state": state,
        "who": requested_by, "when": now, "why": reason,
    }

    response = {
        "request_id": req_id, "status": "accepted", "state": state,
        "blocking_match_id": blocking_match,
        "registration": reg_out,
        "audit_entry": audit_entry,
    }

    await db.execute(text(
        "INSERT INTO roster_audit (id, league_id, player_id, action, from_squad, to_squad, effective_date, who, why, when_, response) "
        "VALUES (:id,:lid,:pid,:action,:from_sq,:to_sq,:edate,:who,:why,:when_,:response)"
    ), {"id": req_id, "lid": league_id, "pid": player_id, "action": transfer_type,
        "from_sq": from_squad, "to_sq": to_squad, "edate": effective_date_str,
        "who": requested_by, "why": reason, "when_": now, "response": json.dumps(response)})

    await db.commit()
    return response


async def history(db: AsyncSession, player_id: str, as_of: str = None) -> dict:
    player_row = await db.execute(text("SELECT id FROM players WHERE id=:id"), {"id": player_id})
    if not player_row.fetchone():
        raise HTTPException(404, detail={"error": {"code": "PLAYER_NOT_FOUND", "message": f"Player {player_id} not found.", "details": {}}})

    today_str = as_of or date.today().isoformat()

    reg_row = await db.execute(text(
        "SELECT squad_id, parent_squad_id, league_id, loan_end_date FROM player_registrations WHERE player_id=:pid LIMIT 1"
    ), {"pid": player_id})
    reg = reg_row.fetchone()

    current_squad = None
    parent_squad = None
    league_id = None
    if reg:
        league_id = reg[2]
        loan_end = reg[3]
        if reg[1] and loan_end and today_str > loan_end:
            # Loan expired — return to parent
            current_squad = reg[1]
            parent_squad = None
        else:
            current_squad = reg[0]
            parent_squad = reg[1]

    audit_rows = await db.execute(text(
        "SELECT id, action, from_squad, to_squad, effective_date, who, why, when_ "
        "FROM roster_audit WHERE player_id=:pid ORDER BY when_ ASC"
    ), {"pid": player_id})

    history_entries = []
    for row in audit_rows.fetchall():
        # Auto-return for expired loans
        audit_entry = {
            "audit_id": row[0], "action": row[1], "player_id": player_id,
            "league_id": league_id, "from_squad_id": row[2], "to_squad_id": row[3],
            "effective_date": row[4], "who": row[5], "why": row[6], "when": row[7],
        }
        history_entries.append(audit_entry)

        # If this was a loan and loan_end_date passed, add loan_return entry
        if row[1] == "loan":
            reg2 = await db.execute(text(
                "SELECT loan_end_date FROM player_registrations WHERE player_id=:pid AND squad_id=:sid"
            ), {"pid": player_id, "sid": row[3]})
            r2 = reg2.fetchone()
            if r2 and r2[0] and today_str > r2[0]:
                return_day = _day_after(r2[0])
                return_entry = {
                    "audit_id": f"{row[0]}-return", "action": "loan_return",
                    "player_id": player_id, "league_id": league_id,
                    "from_squad_id": row[3], "to_squad_id": row[2],
                    "effective_date": return_day, "who": "system", "why": "Loan period ended", "when": return_day + "T00:00:00Z",
                }
                if return_entry not in history_entries:
                    history_entries.append(return_entry)

    return {
        "player_id": player_id,
        "as_of": today_str,
        "league_id": league_id,
        "current_squad_id": current_squad,
        "parent_squad_id": parent_squad,
        "history": history_entries,
    }


def _day_after(date_str: str) -> str:
    from datetime import date, timedelta
    d = date.fromisoformat(date_str)
    return (d + timedelta(days=1)).isoformat()
