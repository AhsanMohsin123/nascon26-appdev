"""Standings engine — recomputed from scratch on every call."""
import hashlib
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.domain.scoring import get_score


async def compute_standings(db: AsyncSession, league_id: str) -> dict:
    league_row = await db.execute(text("SELECT config, sport_id FROM leagues WHERE id = :id"), {"id": league_id})
    league = league_row.fetchone()
    if not league:
        raise HTTPException(404, {"error": {"code": "LEAGUE_NOT_FOUND", "message": f"League {league_id} not found.", "details": {}}})

    import json
    config = json.loads(league[0]) if league[0] else {}
    sport_id = league[1]

    teams_row = await db.execute(text("SELECT team_id FROM league_teams WHERE league_id = :lid"), {"lid": league_id})
    teams = [r[0] for r in teams_row.fetchall()]

    points_cfg = config.get("points", {"win": 3, "draw": 1, "loss": 0})
    qualification_spots = config.get("qualification", {}).get("spots", 1)
    lots_seed = config.get("lots_seed", 42)

    matches_row = await db.execute(text("SELECT id FROM matches WHERE league_id = :lid"), {"lid": league_id})
    match_ids = [r[0] for r in matches_row.fetchall()]

    stats = {t: {"played": 0, "won": 0, "drawn": 0, "lost": 0, "scored": 0, "conceded": 0, "points": 0, "fair_play": 0} for t in teams}
    h2h = {a: {b: {"played": 0, "points": 0, "scored": 0, "conceded": 0} for b in teams if b != a} for a in teams}
    remaining = {t: 0 for t in teams}

    for mid in match_ids:
        score = await get_score(db, mid)
        if score["status"] != "completed" or score["outcome"] == "undecided":
            for t in teams:
                if score["home"]["team_id"] == t or score["away"]["team_id"] == t:
                    remaining[t] = remaining.get(t, 0) + 1
            continue

        home_id = score["home"]["team_id"]
        away_id = score["away"]["team_id"]
        if home_id not in stats or away_id not in stats:
            continue

        hs = score["home"]["score"]
        as_ = score["away"]["score"]
        outcome = score["outcome"]

        stats[home_id]["played"] += 1
        stats[away_id]["played"] += 1
        stats[home_id]["scored"] += hs
        stats[home_id]["conceded"] += as_
        stats[away_id]["scored"] += as_
        stats[away_id]["conceded"] += hs
        stats[home_id]["fair_play"] += score["home"]["fair_play"]
        stats[away_id]["fair_play"] += score["away"]["fair_play"]

        if outcome == "home_win":
            stats[home_id]["won"] += 1
            stats[away_id]["lost"] += 1
            stats[home_id]["points"] += points_cfg.get("win", 3)
            stats[away_id]["points"] += points_cfg.get("loss", 0)
            h2h[home_id][away_id]["points"] += points_cfg.get("win", 3)
            h2h[away_id][home_id]["points"] += points_cfg.get("loss", 0)
        elif outcome == "away_win":
            stats[away_id]["won"] += 1
            stats[home_id]["lost"] += 1
            stats[away_id]["points"] += points_cfg.get("win", 3)
            stats[home_id]["points"] += points_cfg.get("loss", 0)
            h2h[away_id][home_id]["points"] += points_cfg.get("win", 3)
            h2h[home_id][away_id]["points"] += points_cfg.get("loss", 0)
        else:
            stats[home_id]["drawn"] += 1
            stats[away_id]["drawn"] += 1
            stats[home_id]["points"] += points_cfg.get("draw", 1)
            stats[away_id]["points"] += points_cfg.get("draw", 1)
            h2h[home_id][away_id]["points"] += points_cfg.get("draw", 1)
            h2h[away_id][home_id]["points"] += points_cfg.get("draw", 1)

        h2h[home_id][away_id]["played"] += 1
        h2h[away_id][home_id]["played"] += 1
        h2h[home_id][away_id]["scored"] += hs
        h2h[home_id][away_id]["conceded"] += as_
        h2h[away_id][home_id]["scored"] += as_
        h2h[away_id][home_id]["conceded"] += hs

    sorted_teams = sorted(teams, key=lambda t: -stats[t]["points"])
    win_pts = points_cfg.get("win", 3)

    table = []
    for i, t in enumerate(sorted_teams):
        s = stats[t]
        diff = s["scored"] - s["conceded"]
        max_pts = s["points"] + win_pts * remaining[t]

        clinched = sum(1 for x in teams if x != t and (stats[x]["points"] + win_pts * remaining[x]) >= s["points"]) < qualification_spots
        eliminated = sum(1 for x in teams if x != t and stats[x]["points"] > max_pts) >= qualification_spots

        if clinched:
            qual_status = "clinched"
        elif eliminated:
            qual_status = "eliminated"
        else:
            qual_status = "still_possible"

        table.append({
            "rank": i + 1,
            "team_id": t,
            "played": s["played"],
            "won": s["won"],
            "drawn": s["drawn"],
            "lost": s["lost"],
            "scored": s["scored"],
            "conceded": s["conceded"],
            "diff": diff,
            "points": s["points"],
            "fair_play": s["fair_play"],
            "status": qual_status,
            "resolved_by": None,
        })

    return {
        "league_id": league_id,
        "sport_id": sport_id,
        "qualification_spots": qualification_spots,
        "table": table,
        "h2h": h2h,
    }
