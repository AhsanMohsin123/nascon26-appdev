"""Event-sourced scoring engine — append-only log, no mutable counters."""
import json
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.auth.jwt import sign_payload


VALID_TRANSITIONS = {
    "upcoming": {"match_start"},
    "in_progress": {"score", "discipline", "tiebreak_winner", "match_end", "compensation"},
    "completed": {"compensation"},
}


async def append_event(db: AsyncSession, body: dict) -> dict:
    event_id = body.get("event_id")
    match_id = body.get("match_id")
    event_type = body.get("type")
    payload = body.get("payload", {})

    if not event_id or not match_id or not event_type:
        raise HTTPException(400, {"error": {"code": "VALIDATION_ERROR", "message": "Missing required fields", "details": {"fields": []}}})

    existing_event = await db.execute(text("SELECT payload FROM match_events WHERE id = :id"), {"id": event_id})
    existing_row = existing_event.fetchone()
    if existing_row:
        stored_payload = json.loads(existing_row[0]) if existing_row[0] else {}
        if stored_payload != payload or body.get("match_id") != match_id:
            raise HTTPException(409, {"error": {"code": "DUPLICATE_EVENT_ID", "message": f"Event {event_id} already exists with different body.", "details": {}}})
        seq_row = await db.execute(text("SELECT sequence, match_version FROM match_events WHERE id = :id"), {"id": event_id})
        sr = seq_row.fetchone()
        sig = sign_payload(event_id, payload)
        return {"event_id": event_id, "match_id": match_id, "type": event_type, "sequence": sr[0], "match_version": sr[1], "signature": sig}

    match_row = await db.execute(text("SELECT status, sport_id FROM matches WHERE id = :id"), {"id": match_id})
    match = match_row.fetchone()

    if event_type == "match_init":
        if match:
            raise HTTPException(409, {"error": {"code": "MATCH_EXISTS", "message": f"Match {match_id} already exists.", "details": {}}})
        sport_id = payload.get("sport_id")
        home = payload.get("home_team_id")
        away = payload.get("away_team_id")
        league_id = payload.get("league_id")
        await db.execute(text(
            "INSERT INTO matches (id, league_id, sport_id, home_team_id, away_team_id, status) VALUES (:id, :league_id, :sport_id, :home, :away, 'upcoming')"
        ), {"id": match_id, "league_id": league_id, "sport_id": sport_id, "home": home, "away": away})
        await db.commit()
        match_row2 = await db.execute(text("SELECT status FROM matches WHERE id = :id"), {"id": match_id})
        match = match_row2.fetchone()

    if not match:
        raise HTTPException(404, {"error": {"code": "MATCH_NOT_FOUND", "message": f"Match {match_id} not found.", "details": {}}})

    status = match[0]
    allowed = VALID_TRANSITIONS.get(status, set())

    if event_type not in allowed and event_type != "match_init":
        if event_type == "score" and status != "in_progress":
            raise HTTPException(409, {"error": {"code": "MATCH_NOT_IN_PROGRESS", "message": "Match is not in progress.", "details": {}}})
        raise HTTPException(409, {"error": {"code": "ILLEGAL_TRANSITION", "message": f"Cannot apply {event_type} when status is {status}.", "details": {}}})

    if event_type == "match_start":
        await db.execute(text("UPDATE matches SET status = 'in_progress' WHERE id = :id"), {"id": match_id})
    elif event_type == "match_end":
        await db.execute(text("UPDATE matches SET status = 'completed' WHERE id = :id"), {"id": match_id})

    seq_row = await db.execute(text("SELECT COUNT(*) FROM match_events WHERE match_id = :mid"), {"mid": match_id})
    seq = seq_row.scalar() + 1

    sig = sign_payload(event_id, payload)
    await db.execute(text(
        "INSERT INTO match_events (id, match_id, sequence, type, payload, signature) VALUES (:id, :mid, :seq, :type, :payload, :sig)"
    ), {"id": event_id, "mid": match_id, "seq": seq, "type": event_type, "payload": json.dumps(payload), "sig": sig})
    await db.commit()

    return {"event_id": event_id, "match_id": match_id, "type": event_type, "sequence": seq, "match_version": seq, "signature": sig}


async def get_score(db: AsyncSession, match_id: str) -> dict:
    match_row = await db.execute(text("SELECT sport_id, league_id, status, home_team_id, away_team_id FROM matches WHERE id = :id"), {"id": match_id})
    match = match_row.fetchone()
    if not match:
        raise HTTPException(404, {"error": {"code": "MATCH_NOT_FOUND", "message": f"Match {match_id} not found.", "details": {}}})

    sport_id, league_id, status, home_id, away_id = match

    events_row = await db.execute(text("SELECT id, sequence, type, payload, signature FROM match_events WHERE match_id = :mid ORDER BY sequence"), {"mid": match_id})
    events = events_row.fetchall()

    home_score = 0
    away_score = 0
    home_fair = 0
    away_fair = 0
    tiebreak_winner = None
    compensated_ids = set()
    compensated_by_map = {}

    for ev in events:
        if ev[2] == "compensation":
            p = json.loads(ev[3]) if ev[3] else {}
            target = p.get("compensates")
            if target:
                compensated_ids.add(target)
                compensated_by_map[target] = ev[0]

    for ev in events:
        eid, seq, etype, epayload_str, sig = ev
        payload = json.loads(epayload_str) if epayload_str else {}
        if eid in compensated_ids:
            continue
        if etype == "score":
            team = payload.get("team_id")
            if team == home_id:
                home_score += 1
            elif team == away_id:
                away_score += 1
        elif etype == "discipline":
            team = payload.get("team_id")
            pts = payload.get("points", 0)
            if team == home_id:
                home_fair += pts
            elif team == away_id:
                away_fair += pts
        elif etype == "tiebreak_winner":
            tiebreak_winner = payload.get("team_id")

    if status == "completed":
        if home_score > away_score:
            outcome = "home_win"
            winner = home_id
        elif away_score > home_score:
            outcome = "away_win"
            winner = away_id
        elif tiebreak_winner:
            outcome = "home_win" if tiebreak_winner == home_id else "away_win"
            winner = tiebreak_winner
        else:
            outcome = "draw"
            winner = None
    else:
        outcome = "pending"
        winner = None

    events_out = []
    for ev in events:
        eid, seq, etype, epayload_str, sig = ev
        payload = json.loads(epayload_str) if epayload_str else {}
        events_out.append({
            "sequence": seq,
            "event_id": eid,
            "type": etype,
            "payload": payload,
            "signature": sig,
            "compensated": eid in compensated_ids,
            "compensated_by": compensated_by_map.get(eid),
        })

    return {
        "match_id": match_id,
        "sport_id": sport_id,
        "league_id": league_id,
        "status": status,
        "outcome": outcome,
        "winner_team_id": winner,
        "tiebreak_winner_team_id": tiebreak_winner,
        "home": {"team_id": home_id, "score": home_score, "wickets": None, "balls": None, "overs": None, "fair_play": home_fair},
        "away": {"team_id": away_id, "score": away_score, "wickets": None, "balls": None, "overs": None, "fair_play": away_fair},
        "version": len(events),
        "events": events_out,
    }
