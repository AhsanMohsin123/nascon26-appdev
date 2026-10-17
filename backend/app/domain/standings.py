"""Standings — recomputed from scratch from event log on every call, full tie-breaker chain."""
import hashlib
import json
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.domain.scoring import get_score


async def compute_standings(db: AsyncSession, league_id: str) -> dict:
    league_row = await db.execute(text("SELECT config, sport_id FROM leagues WHERE id=:id"), {"id": league_id})
    league = league_row.fetchone()
    if not league:
        raise HTTPException(404, detail={"error": {"code": "LEAGUE_NOT_FOUND", "message": f"League {league_id} not found.", "details": {}}})

    config = json.loads(league[0]) if league[0] else {}
    sport_id = league[1]

    sport_cfg_row = await db.execute(text("SELECT config FROM sports WHERE id=:id"), {"id": sport_id})
    scr = sport_cfg_row.fetchone()
    sport_cfg = json.loads(scr[0]) if scr else {}
    model = sport_cfg.get("scoring_model", "event")
    bpo = sport_cfg.get("periods", {}).get("balls_per_over", 6)

    teams_row = await db.execute(text("SELECT team_id FROM league_teams WHERE league_id=:lid"), {"lid": league_id})
    teams = [r[0] for r in teams_row.fetchall()]
    if not teams:
        raise HTTPException(404, detail={"error": {"code": "LEAGUE_NOT_FOUND", "message": f"League {league_id} has no teams.", "details": {}}})

    points_cfg = config.get("points", {"win": 3, "draw": 1, "loss": 0})
    win_pts = points_cfg.get("win", 3)
    draw_pts = points_cfg.get("draw", 1)
    loss_pts = points_cfg.get("loss", 0)
    qualification_spots = config.get("qualification", {}).get("spots", 1)
    lots_seed = config.get("lots_seed", 42)
    tie_break_order = config.get("tie_break_order", sport_cfg.get("tie_break_order",
        ["h2h_points", "h2h_diff", "overall_diff", "scored", "fair_play", "draw_lots"]))
    if "draw_lots" not in tie_break_order:
        tie_break_order = [t for t in tie_break_order if t != "draw_lots"] + ["draw_lots"]

    matches_row = await db.execute(text("SELECT id FROM matches WHERE league_id=:lid"), {"lid": league_id})
    match_ids = [r[0] for r in matches_row.fetchall()]

    stats = {t: {"played": 0, "won": 0, "drawn": 0, "lost": 0,
                 "scored": 0, "conceded": 0, "points": 0, "fair_play": 0,
                 "legal_balls_faced": 0, "legal_balls_bowled": 0,
                 "runs_scored": 0, "runs_conceded": 0} for t in teams}
    h2h = {a: {b: {"played": 0, "points": 0, "scored": 0, "conceded": 0,
                   "legal_balls_faced": 0, "legal_balls_bowled": 0,
                   "runs_scored": 0, "runs_conceded": 0}
               for b in teams if b != a} for a in teams}
    remaining = {t: 0 for t in teams}

    for mid in match_ids:
        score_data = await get_score(db, mid)
        home_id = score_data["home"]["team_id"]
        away_id = score_data["away"]["team_id"]
        status = score_data["status"]
        outcome = score_data["outcome"]

        if status != "completed" or outcome == "undecided" or outcome == "pending":
            if home_id in remaining:
                remaining[home_id] = remaining.get(home_id, 0) + 1
            if away_id in remaining:
                remaining[away_id] = remaining.get(away_id, 0) + 1
            continue

        if home_id not in stats or away_id not in stats:
            continue

        hs = score_data["home"]["score"]
        as_ = score_data["away"]["score"]
        hf = score_data["home"]["fair_play"]
        af = score_data["away"]["fair_play"]

        stats[home_id]["played"] += 1
        stats[away_id]["played"] += 1
        stats[home_id]["fair_play"] += hf
        stats[away_id]["fair_play"] += af

        if model == "innings":
            hb = score_data["home"]["balls"] or 0
            ab = score_data["away"]["balls"] or 0
            stats[home_id]["runs_scored"] += hs
            stats[home_id]["runs_conceded"] += as_
            stats[home_id]["legal_balls_faced"] += hb
            stats[home_id]["legal_balls_bowled"] += ab
            stats[away_id]["runs_scored"] += as_
            stats[away_id]["runs_conceded"] += hs
            stats[away_id]["legal_balls_faced"] += ab
            stats[away_id]["legal_balls_bowled"] += hb
            h2h[home_id][away_id]["runs_scored"] += hs
            h2h[home_id][away_id]["runs_conceded"] += as_
            h2h[home_id][away_id]["legal_balls_faced"] += hb
            h2h[home_id][away_id]["legal_balls_bowled"] += ab
            h2h[away_id][home_id]["runs_scored"] += as_
            h2h[away_id][home_id]["runs_conceded"] += hs
            h2h[away_id][home_id]["legal_balls_faced"] += ab
            h2h[away_id][home_id]["legal_balls_bowled"] += hb
            stats[home_id]["scored"] += hs
            stats[home_id]["conceded"] += as_
            stats[away_id]["scored"] += as_
            stats[away_id]["conceded"] += hs
        else:
            stats[home_id]["scored"] += hs
            stats[home_id]["conceded"] += as_
            stats[away_id]["scored"] += as_
            stats[away_id]["conceded"] += hs
            h2h[home_id][away_id]["scored"] += hs
            h2h[home_id][away_id]["conceded"] += as_
            h2h[away_id][home_id]["scored"] += as_
            h2h[away_id][home_id]["conceded"] += hs

        h2h[home_id][away_id]["played"] += 1
        h2h[away_id][home_id]["played"] += 1

        if outcome == "home_win":
            stats[home_id]["won"] += 1
            stats[away_id]["lost"] += 1
            stats[home_id]["points"] += win_pts
            stats[away_id]["points"] += loss_pts
            h2h[home_id][away_id]["points"] += win_pts
            h2h[away_id][home_id]["points"] += loss_pts
        elif outcome == "away_win":
            stats[away_id]["won"] += 1
            stats[home_id]["lost"] += 1
            stats[away_id]["points"] += win_pts
            stats[home_id]["points"] += loss_pts
            h2h[away_id][home_id]["points"] += win_pts
            h2h[home_id][away_id]["points"] += loss_pts
        else:  # draw
            stats[home_id]["drawn"] += 1
            stats[away_id]["drawn"] += 1
            stats[home_id]["points"] += draw_pts
            stats[away_id]["points"] += draw_pts
            h2h[home_id][away_id]["points"] += draw_pts
            h2h[away_id][home_id]["points"] += draw_pts

    def calc_diff(t, group_teams=None, h2h_only=False):
        if h2h_only and group_teams:
            opponents = [x for x in group_teams if x != t]
            if model == "innings":
                rs = sum(h2h[t][o]["runs_scored"] for o in opponents if o in h2h.get(t, {}))
                rc = sum(h2h[t][o]["runs_conceded"] for o in opponents if o in h2h.get(t, {}))
                bf = sum(h2h[t][o]["legal_balls_faced"] for o in opponents if o in h2h.get(t, {}))
                bb = sum(h2h[t][o]["legal_balls_bowled"] for o in opponents if o in h2h.get(t, {}))
                overs_f = bf / bpo if bf else 0
                overs_b = bb / bpo if bb else 0
                nrr = (rs / overs_f if overs_f else 0) - (rc / overs_b if overs_b else 0)
                return round(nrr, 3)
            else:
                sc = sum(h2h[t][o]["scored"] for o in opponents if o in h2h.get(t, {}))
                co = sum(h2h[t][o]["conceded"] for o in opponents if o in h2h.get(t, {}))
                return sc - co
        else:
            if model == "innings":
                rs = stats[t]["runs_scored"]
                rc = stats[t]["runs_conceded"]
                bf = stats[t]["legal_balls_faced"]
                bb = stats[t]["legal_balls_bowled"]
                periods = sport_cfg.get("periods", {})
                max_overs = periods.get("overs_per_innings", 20)
                # Use max overs if innings ended by all-out
                overs_f = bf / bpo if bf else 0
                overs_b = bb / bpo if bb else 0
                nrr = (rs / overs_f if overs_f else 0) - (rc / overs_b if overs_b else 0)
                return round(nrr, 3)
            else:
                return stats[t]["scored"] - stats[t]["conceded"]

    def lots_key(t):
        return hashlib.sha256(f"{lots_seed}|{league_id}|{t}".encode("utf-8")).hexdigest()

    def resolve(group: list, depth=0) -> list:
        if len(group) <= 1:
            return group
        for criterion in tie_break_order:
            if criterion == "h2h_points":
                vals = {t: sum(h2h[t].get(o, {}).get("points", 0) for o in group if o != t) for t in group}
            elif criterion == "h2h_diff":
                vals = {t: calc_diff(t, group, h2h_only=True) for t in group}
            elif criterion == "overall_diff":
                vals = {t: calc_diff(t) for t in group}
            elif criterion == "scored":
                vals = {t: stats[t]["scored"] for t in group}
            elif criterion == "fair_play":
                vals = {t: stats[t]["fair_play"] for t in group}
            elif criterion == "draw_lots":
                return sorted(group, key=lots_key)
            else:
                continue

            unique_vals = sorted(set(vals.values()), reverse=True)
            if len(unique_vals) == 1:
                continue

            result = []
            for val in unique_vals:
                sub = [t for t in group if vals[t] == val]
                if len(sub) > 1:
                    result.extend(resolve(sub, depth + 1))
                else:
                    result.extend(sub)
            return result

        return sorted(group, key=lots_key)

    # Sort by points, then resolve ties
    by_points = {}
    for t in teams:
        p = stats[t]["points"]
        by_points.setdefault(p, []).append(t)

    sorted_teams = []
    resolved_by = {}
    for pts in sorted(by_points.keys(), reverse=True):
        group = by_points[pts]
        if len(group) == 1:
            sorted_teams.extend(group)
        else:
            ordered = resolve(group)
            for i, t in enumerate(ordered):
                if i < len(ordered) - 1:
                    resolved_by[t] = _find_criterion(t, ordered[i+1], group, tie_break_order, stats, h2h, calc_diff, lots_key)
            sorted_teams.extend(ordered)

    # Qualification status (points-only per spec)
    table = []
    for rank, t in enumerate(sorted_teams, 1):
        s = stats[t]
        diff = calc_diff(t)
        max_pts = s["points"] + win_pts * remaining.get(t, 0)

        clinched = sum(1 for x in teams if x != t and
                       (stats[x]["points"] + win_pts * remaining.get(x, 0)) >= s["points"]) < qualification_spots
        eliminated = sum(1 for x in teams if x != t and stats[x]["points"] > max_pts) >= qualification_spots

        status_str = "clinched" if clinched else ("eliminated" if eliminated else "still_possible")

        table.append({
            "rank": rank,
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
            "status": status_str,
            "resolved_by": resolved_by.get(t),
        })

    return {
        "league_id": league_id,
        "sport_id": sport_id,
        "qualification_spots": qualification_spots,
        "table": table,
        "h2h": {a: {b: {"played": h2h[a][b]["played"], "points": h2h[a][b]["points"],
                         "scored": h2h[a][b]["scored"], "conceded": h2h[a][b]["conceded"]}
                    for b in teams if b != a} for a in teams},
    }


def _find_criterion(t1, t2, group, order, stats, h2h, calc_diff, lots_key):
    for criterion in order:
        if criterion == "h2h_points":
            v1 = sum(h2h[t1].get(o, {}).get("points", 0) for o in group if o != t1)
            v2 = sum(h2h[t2].get(o, {}).get("points", 0) for o in group if o != t2)
        elif criterion == "h2h_diff":
            v1 = calc_diff(t1, group, h2h_only=True)
            v2 = calc_diff(t2, group, h2h_only=True)
        elif criterion == "overall_diff":
            v1 = calc_diff(t1)
            v2 = calc_diff(t2)
        elif criterion == "scored":
            v1 = stats[t1]["scored"]
            v2 = stats[t2]["scored"]
        elif criterion == "fair_play":
            v1 = stats[t1]["fair_play"]
            v2 = stats[t2]["fair_play"]
        elif criterion == "draw_lots":
            return "draw_lots"
        else:
            continue
        if v1 != v2:
            return criterion
    return "draw_lots"
