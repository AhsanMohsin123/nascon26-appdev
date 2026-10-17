"""Event-sourced scoring engine — append-only log, score rebuilt from events every read."""
import json
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.auth.jwt import sign_payload


async def append_event(db: AsyncSession, body: dict) -> dict:
    event_id = body.get("event_id")
    match_id = body.get("match_id")
    event_type = body.get("type")
    payload = body.get("payload", {})

    if not event_id or not match_id or not event_type:
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Missing required fields", "details": {"fields": ["event_id", "match_id", "type"]}}})

    # Idempotency
    existing = await db.execute(text("SELECT type, payload, match_id FROM match_events WHERE id = :id"), {"id": event_id})
    existing_row = existing.fetchone()
    if existing_row:
        stored_type, stored_payload_str, stored_match = existing_row
        stored_payload = json.loads(stored_payload_str) if stored_payload_str else {}
        if stored_type != event_type or stored_payload != payload or stored_match != match_id:
            raise HTTPException(409, detail={"error": {"code": "DUPLICATE_EVENT_ID", "message": f"Event {event_id} reused with different body.", "details": {}}})
        seq_row = await db.execute(text("SELECT sequence FROM match_events WHERE id = :id"), {"id": event_id})
        seq = seq_row.scalar()
        ver_row = await db.execute(text("SELECT COUNT(*) FROM match_events WHERE match_id = :mid"), {"mid": match_id})
        ver = ver_row.scalar()
        sig = sign_payload(event_id, payload)
        return {"event_id": event_id, "match_id": match_id, "type": event_type, "sequence": seq, "match_version": ver, "signature": sig}

    # match_init — creates the match
    if event_type == "match_init":
        existing_match = await db.execute(text("SELECT id FROM matches WHERE id = :id"), {"id": match_id})
        if existing_match.fetchone():
            raise HTTPException(409, detail={"error": {"code": "MATCH_EXISTS", "message": f"Match {match_id} already exists.", "details": {}}})
        sport_id = payload.get("sport_id")
        sport_row = await db.execute(text("SELECT id FROM sports WHERE id = :id"), {"id": sport_id})
        if not sport_row.fetchone():
            raise HTTPException(404, detail={"error": {"code": "SPORT_NOT_FOUND", "message": f"Sport {sport_id} not found.", "details": {}}})
        home = payload.get("home_team_id")
        away = payload.get("away_team_id")
        league_id = payload.get("league_id")
        await db.execute(text(
            "INSERT INTO matches (id, league_id, sport_id, home_team_id, away_team_id, status) VALUES (:id, :league_id, :sport_id, :home, :away, 'upcoming')"
        ), {"id": match_id, "league_id": league_id, "sport_id": sport_id, "home": home, "away": away})

    # Fetch match
    match_row = await db.execute(text("SELECT status, sport_id, home_team_id, away_team_id FROM matches WHERE id = :id"), {"id": match_id})
    match = match_row.fetchone()
    if not match:
        raise HTTPException(404, detail={"error": {"code": "MATCH_NOT_FOUND", "message": f"Match {match_id} not found.", "details": {}}})

    status, sport_id, home_id, away_id = match

    # Validate transitions
    if event_type == "match_start":
        if status != "upcoming":
            raise HTTPException(409, detail={"error": {"code": "ILLEGAL_TRANSITION", "message": f"Cannot start match with status {status}.", "details": {}}})
        await db.execute(text("UPDATE matches SET status='in_progress' WHERE id=:id"), {"id": match_id})

    elif event_type in ("score", "discipline", "tiebreak_winner"):
        if status != "in_progress":
            raise HTTPException(409, detail={"error": {"code": "MATCH_NOT_IN_PROGRESS", "message": "Match is not in progress.", "details": {}}})

        if event_type == "score":
            team = payload.get("team_id")
            if team not in (home_id, away_id):
                raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": f"team_id must be home or away.", "details": {"fields": ["team_id"]}}})
            # Validate event_type against sport config
            sport_cfg_row = await db.execute(text("SELECT config FROM sports WHERE id=:id"), {"id": sport_id})
            sport_cfg = json.loads(sport_cfg_row.fetchone()[0])
            event_name = payload.get("event_type")
            if event_name not in sport_cfg.get("scoring_events", {}):
                raise HTTPException(400, detail={"error": {"code": "UNKNOWN_EVENT_TYPE", "message": f"Event type {event_name} not defined for sport {sport_id}.", "details": {}}})
            # Check innings/round limits
            await _check_model_limits(db, sport_cfg, match_id, team, event_name)

    elif event_type == "match_end":
        if status != "in_progress":
            raise HTTPException(409, detail={"error": {"code": "ILLEGAL_TRANSITION", "message": "Match must be in_progress to end.", "details": {}}})
        # Check tie allowed
        sport_cfg_row = await db.execute(text("SELECT config FROM sports WHERE id=:id"), {"id": sport_id})
        sport_cfg = json.loads(sport_cfg_row.fetchone()[0])
        score = await _compute_score_from_log(db, match_id, sport_id, home_id, away_id, sport_cfg)
        h_score = score["home_score"]
        a_score = score["away_score"]
        draw_allowed = sport_cfg.get("draw_allowed", True)
        tiebreak = score.get("tiebreak_winner")
        if h_score == a_score and not draw_allowed and not tiebreak:
            raise HTTPException(409, detail={"error": {"code": "TIE_NOT_ALLOWED", "message": "Draw not allowed for this sport.", "details": {}}})
        await db.execute(text("UPDATE matches SET status='completed' WHERE id=:id"), {"id": match_id})

    elif event_type == "compensation":
        if status == "upcoming":
            raise HTTPException(409, detail={"error": {"code": "ILLEGAL_TRANSITION", "message": "Cannot compensate before match starts.", "details": {}}})
        target_id = payload.get("compensates")
        target_row = await db.execute(text("SELECT type, match_id FROM match_events WHERE id=:id"), {"id": target_id})
        target = target_row.fetchone()
        if not target:
            raise HTTPException(404, detail={"error": {"code": "EVENT_NOT_FOUND", "message": f"Event {target_id} not found.", "details": {}}})
        if target[1] != match_id:
            raise HTTPException(409, detail={"error": {"code": "INVALID_COMPENSATION", "message": "Event belongs to a different match.", "details": {}}})
        if target[0] not in ("score", "discipline", "tiebreak_winner"):
            raise HTTPException(409, detail={"error": {"code": "INVALID_COMPENSATION", "message": "Can only compensate score/discipline/tiebreak_winner events.", "details": {}}})
        already = await db.execute(text("SELECT id FROM match_events WHERE type='compensation' AND payload::jsonb->>'compensates'=:tid"), {"tid": target_id})
        if already.fetchone():
            raise HTTPException(409, detail={"error": {"code": "INVALID_COMPENSATION", "message": f"Event {target_id} already compensated.", "details": {}}})

    elif event_type != "match_init":
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": f"Unknown event type {event_type}.", "details": {"fields": ["type"]}}})

    # Append to log
    seq_row = await db.execute(text("SELECT COUNT(*) FROM match_events WHERE match_id=:mid"), {"mid": match_id})
    seq = (seq_row.scalar() or 0) + 1
    sig = sign_payload(event_id, payload)

    await db.execute(text(
        "INSERT INTO match_events (id, match_id, sequence, type, payload, signature) VALUES (:id, :mid, :seq, :type, :payload, :sig)"
    ), {"id": event_id, "mid": match_id, "seq": seq, "type": event_type, "payload": json.dumps(payload), "sig": sig})
    await db.commit()

    return {"event_id": event_id, "match_id": match_id, "type": event_type, "sequence": seq, "match_version": seq, "signature": sig}


async def _check_model_limits(db: AsyncSession, sport_cfg: dict, match_id: str, team_id: str, event_name: str):
    model = sport_cfg.get("scoring_model")
    events_row = await db.execute(text(
        "SELECT type, payload FROM match_events WHERE match_id=:mid ORDER BY sequence"
    ), {"mid": match_id})
    all_events = events_row.fetchall()

    compensated = set()
    for ev in all_events:
        if ev[0] == "compensation":
            p = json.loads(ev[1]) if ev[1] else {}
            compensated.add(p.get("compensates"))

    if model == "innings":
        periods = sport_cfg["periods"]
        max_legal = periods["innings_per_team"] * periods["overs_per_innings"] * periods["balls_per_over"]
        max_wickets = periods["innings_per_team"] * periods["wickets_per_innings"]
        scoring_events = sport_cfg["scoring_events"]

        legal_balls = 0
        wickets = 0
        for ev in all_events:
            if ev[0] != "score" or ev[0] in compensated:
                continue
            eid_check = None
            p = json.loads(ev[1]) if ev[1] else {}
            if p.get("team_id") != team_id:
                continue
            en = p.get("event_type", "")
            if en in scoring_events:
                se = scoring_events[en]
                if se.get("legal_ball"):
                    legal_balls += 1
                if se.get("wicket"):
                    wickets += 1

        if legal_balls >= max_legal or wickets >= max_wickets:
            raise HTTPException(409, detail={"error": {"code": "INNINGS_COMPLETE", "message": f"Innings complete for team {team_id}.", "details": {}}})

    elif model == "round":
        periods = sport_cfg["periods"]
        best_of = periods["best_of"]
        needed = (best_of + 1) // 2
        scoring_events = sport_cfg["scoring_events"]

        rounds_won = 0
        for ev in all_events:
            if ev[0] != "score":
                continue
            p = json.loads(ev[1]) if ev[1] else {}
            if p.get("team_id") != team_id:
                continue
            en = p.get("event_type", "")
            if en in scoring_events:
                rounds_won += scoring_events[en].get("rounds", 0)

        if rounds_won >= needed:
            raise HTTPException(409, detail={"error": {"code": "SERIES_ALREADY_DECIDED", "message": f"Series already decided for team {team_id}.", "details": {}}})


async def _compute_score_from_log(db: AsyncSession, match_id: str, sport_id: str, home_id: str, away_id: str, sport_cfg: dict) -> dict:
    events_row = await db.execute(text(
        "SELECT id, type, payload FROM match_events WHERE match_id=:mid ORDER BY sequence"
    ), {"mid": match_id})
    all_events = events_row.fetchall()

    compensated = set()
    comp_by = {}
    for ev in all_events:
        if ev[1] == "compensation":
            p = json.loads(ev[2]) if ev[2] else {}
            t = p.get("compensates")
            if t:
                compensated.add(t)
                comp_by[t] = ev[0]

    model = sport_cfg.get("scoring_model", "event")
    scoring_events_cfg = sport_cfg.get("scoring_events", {})

    home_score = away_score = 0
    home_fair = away_fair = 0
    home_balls = away_balls = 0
    home_wickets = away_wickets = 0
    tiebreak_winner = None

    for ev in all_events:
        eid, etype, epayload_str = ev
        if eid in compensated:
            continue
        payload = json.loads(epayload_str) if epayload_str else {}

        if etype == "score":
            team = payload.get("team_id")
            en = payload.get("event_type", "")
            se = scoring_events_cfg.get(en, {})

            if model == "event":
                pts = se.get("points", 0)
                if team == home_id:
                    home_score += pts
                else:
                    away_score += pts
            elif model == "innings":
                runs = se.get("runs", 0)
                legal = se.get("legal_ball", False)
                wicket = se.get("wicket", False)
                if team == home_id:
                    home_score += runs
                    if legal:
                        home_balls += 1
                    if wicket:
                        home_wickets += 1
                else:
                    away_score += runs
                    if legal:
                        away_balls += 1
                    if wicket:
                        away_wickets += 1
            elif model == "round":
                rounds = se.get("rounds", 0)
                if team == home_id:
                    home_score += rounds
                else:
                    away_score += rounds

        elif etype == "discipline":
            team = payload.get("team_id")
            pts = payload.get("points", 0)
            if team == home_id:
                home_fair += pts
            else:
                away_fair += pts

        elif etype == "tiebreak_winner":
            tiebreak_winner = payload.get("team_id")

    return {
        "home_score": home_score,
        "away_score": away_score,
        "home_fair": home_fair,
        "away_fair": away_fair,
        "home_balls": home_balls,
        "away_balls": away_balls,
        "home_wickets": home_wickets,
        "away_wickets": away_wickets,
        "tiebreak_winner": tiebreak_winner,
        "compensated": compensated,
        "comp_by": comp_by,
    }


def _overs_str(balls: int, bpo: int) -> str:
    return f"{balls // bpo}.{balls % bpo}"


async def get_score(db: AsyncSession, match_id: str) -> dict:
    match_row = await db.execute(text(
        "SELECT sport_id, league_id, status, home_team_id, away_team_id FROM matches WHERE id=:id"
    ), {"id": match_id})
    match = match_row.fetchone()
    if not match:
        raise HTTPException(404, detail={"error": {"code": "MATCH_NOT_FOUND", "message": f"Match {match_id} not found.", "details": {}}})

    sport_id, league_id, status, home_id, away_id = match

    sport_cfg_row = await db.execute(text("SELECT config FROM sports WHERE id=:id"), {"id": sport_id})
    sport_cfg_r = sport_cfg_row.fetchone()
    sport_cfg = json.loads(sport_cfg_r[0]) if sport_cfg_r else {}
    model = sport_cfg.get("scoring_model", "event")

    computed = await _compute_score_from_log(db, match_id, sport_id, home_id, away_id, sport_cfg)
    h_score = computed["home_score"]
    a_score = computed["away_score"]
    tiebreak = computed["tiebreak_winner"]
    compensated = computed["compensated"]
    comp_by = computed["comp_by"]

    # Determine outcome
    if status == "completed":
        if h_score > a_score:
            outcome, winner = "home_win", home_id
        elif a_score > h_score:
            outcome, winner = "away_win", away_id
        elif tiebreak:
            outcome = "home_win" if tiebreak == home_id else "away_win"
            winner = tiebreak
        else:
            draw_allowed = sport_cfg.get("draw_allowed", True)
            outcome = "draw" if draw_allowed else "undecided"
            winner = None
    else:
        outcome, winner = "pending", None

    # Innings/overs fields
    bpo = sport_cfg.get("periods", {}).get("balls_per_over", 6) if model == "innings" else None
    h_wickets = computed["home_wickets"] if model == "innings" else None
    a_wickets = computed["away_wickets"] if model == "innings" else None
    h_balls = computed["home_balls"] if model == "innings" else None
    a_balls = computed["away_balls"] if model == "innings" else None
    h_overs = _overs_str(h_balls, bpo) if model == "innings" else None
    a_overs = _overs_str(a_balls, bpo) if model == "innings" else None

    # Build events list
    events_row = await db.execute(text(
        "SELECT id, sequence, type, payload, signature FROM match_events WHERE match_id=:mid ORDER BY sequence"
    ), {"mid": match_id})
    events_out = []
    for ev in events_row.fetchall():
        eid, seq, etype, epayload_str, sig = ev
        payload = json.loads(epayload_str) if epayload_str else {}
        events_out.append({
            "sequence": seq,
            "event_id": eid,
            "type": etype,
            "payload": payload,
            "signature": sig,
            "compensated": eid in compensated,
            "compensated_by": comp_by.get(eid),
        })

    return {
        "match_id": match_id,
        "sport_id": sport_id,
        "league_id": league_id,
        "status": status,
        "outcome": outcome,
        "winner_team_id": winner,
        "tiebreak_winner_team_id": tiebreak,
        "home": {"team_id": home_id, "score": h_score, "wickets": h_wickets, "balls": h_balls, "overs": h_overs, "fair_play": computed["home_fair"]},
        "away": {"team_id": away_id, "score": a_score, "wickets": a_wickets, "balls": a_balls, "overs": a_overs, "fair_play": computed["away_fair"]},
        "version": len(events_out),
        "events": events_out,
    }
