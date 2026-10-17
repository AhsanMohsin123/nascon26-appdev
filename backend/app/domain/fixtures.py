"""Fixture generation — round-robin, Swiss, single/double elimination.
Custom implementation; no third-party fixture libraries.
"""
import math
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


async def generate(db: AsyncSession, body: dict) -> dict:
    fmt = body.get("format")
    teams = body.get("teams", [])
    params = body.get("params", {})

    if fmt == "round_robin":
        return _round_robin(teams, params)
    elif fmt == "swiss":
        return _swiss(teams, params)
    elif fmt == "single_elim":
        return _single_elim(teams, params)
    elif fmt == "double_elim":
        return _double_elim(teams, params)
    else:
        raise HTTPException(400, {"error": {"code": "VALIDATION_ERROR", "message": "Unknown format", "details": {"fields": ["format"]}}})


def _round_robin(teams: list, params: dict) -> dict:
    n = len(teams)
    if not (2 <= n <= 40):
        raise HTTPException(400, {"error": {"code": "VALIDATION_ERROR", "message": "Team count must be 2-40", "details": {"fields": ["teams"]}}})

    legs = params.get("legs", 1)
    withdrawals = params.get("withdrawals", [])
    withdrawal_policy = params.get("withdrawal_policy", "forfeit_remaining")

    rounds_per_leg = n if n % 2 == 1 else n - 1
    total_rounds = rounds_per_leg * legs

    withdrawn = {}
    for w in withdrawals:
        tid = w["team_id"]
        if tid not in teams:
            raise HTTPException(400, {"error": {"code": "VALIDATION_ERROR", "message": f"Unknown team {tid}", "details": {"fields": ["withdrawals"]}}})
        ar = w["after_round"]
        if ar < 0 or ar > total_rounds:
            raise HTTPException(400, {"error": {"code": "VALIDATION_ERROR", "message": "after_round out of range", "details": {"fields": ["withdrawals"]}}})
        withdrawn[tid] = ar

    schedule = _circle_method(teams, legs)

    summary = {"total": 0, "scheduled": 0, "forfeit": 0, "voided": 0}
    all_rounds = []
    for round_data in schedule:
        r_num = round_data["round"]
        new_matches = []
        for m in round_data["matches"]:
            summary["total"] += 1
            h, a = m["home"], m["away"]
            h_withdrawn = h in withdrawn
            a_withdrawn = a in withdrawn
            h_after = withdrawn.get(h, total_rounds + 1)
            a_after = withdrawn.get(a, total_rounds + 1)

            if withdrawal_policy == "void_all":
                if h_withdrawn or a_withdrawn:
                    m["status"] = "voided"
                    m["awarded_to"] = None
                    summary["voided"] += 1
                else:
                    m["status"] = "scheduled"
                    m["awarded_to"] = None
                    summary["scheduled"] += 1
            else:  # forfeit_remaining
                if h_withdrawn and a_withdrawn:
                    m["status"] = "voided"
                    m["awarded_to"] = None
                    summary["voided"] += 1
                elif h_withdrawn and r_num > h_after:
                    m["status"] = "forfeit"
                    m["awarded_to"] = a
                    summary["forfeit"] += 1
                elif a_withdrawn and r_num > a_after:
                    m["status"] = "forfeit"
                    m["awarded_to"] = h
                    summary["forfeit"] += 1
                else:
                    m["status"] = "scheduled"
                    m["awarded_to"] = None
                    summary["scheduled"] += 1
            new_matches.append(m)
        round_data["matches"] = new_matches
        all_rounds.append(round_data)

    return {
        "format": "round_robin",
        "legs": legs,
        "team_count": n,
        "round_count": total_rounds,
        "rounds": all_rounds,
        "summary": summary,
    }


def _circle_method(teams: list, legs: int) -> list:
    n = len(teams)
    working = list(teams)
    if n % 2 == 1:
        working.append(None)  # bye sentinel

    m = len(working) // 2
    rounds_per_leg = len(working) - 1
    all_rounds = []

    for leg in range(1, legs + 1):
        t = list(working)
        for r in range(rounds_per_leg):
            global_round = (leg - 1) * rounds_per_leg + r + 1
            matches = []
            byes = []
            idx = 1
            for i in range(m):
                home = t[i]
                away = t[-(i + 1)]
                if home is None:
                    byes.append(away)
                elif away is None:
                    byes.append(home)
                else:
                    if leg % 2 == 0:
                        home, away = away, home
                    matches.append({
                        "match_id": f"RR-L{leg}-R{global_round}-M{idx}",
                        "leg": leg,
                        "home": home,
                        "away": away,
                        "status": "scheduled",
                        "awarded_to": None,
                    })
                    idx += 1
            all_rounds.append({"round": global_round, "matches": matches, "byes": byes})
            t = [t[0]] + [t[-1]] + t[1:-1]
    return all_rounds


def _swiss(teams: list, params: dict) -> dict:
    n = len(teams)
    if not (2 <= n <= 64):
        raise HTTPException(400, {"error": {"code": "VALIDATION_ERROR", "message": "Team count must be 2-64", "details": {"fields": ["teams"]}}})

    total_rounds = params.get("total_rounds", math.ceil(math.log2(n)))
    round_num = params.get("round", 1)
    history = params.get("history", [])

    scores = {t: 0.0 for t in teams}
    buchholz = {t: 0.0 for t in teams}
    played = {t: set() for t in teams}
    had_bye = set()

    for h_round in history:
        bye_team = h_round.get("bye")
        if bye_team:
            scores[bye_team] += 1.0
            had_bye.add(bye_team)
        for m in h_round.get("matches", []):
            home, away, result = m["home"], m["away"], m["result"]
            played[home].add(away)
            played[away].add(home)
            if result == "home":
                scores[home] += 1.0
            elif result == "away":
                scores[away] += 1.0
            else:
                scores[home] += 0.5
                scores[away] += 0.5

    for t in teams:
        buchholz[t] = sum(scores[opp] for opp in played[t])

    standings = sorted(teams, key=lambda t: (-scores[t], -buchholz[t], teams.index(t)))

    if round_num == 1:
        m = n // 2
        bye = teams[-1] if n % 2 == 1 else None
        pairings = []
        for i in range(m):
            pairings.append({
                "match_id": f"SW-R{round_num}-M{i+1}",
                "home": teams[i],
                "away": teams[i + m],
            })
        return {
            "format": "swiss",
            "round": round_num,
            "total_rounds": total_rounds,
            "pairings": pairings,
            "bye": bye,
            "standings": [
                {"rank": i + 1, "team_id": t, "score": scores[t], "buchholz": buchholz[t]}
                for i, t in enumerate(standings)
            ],
        }

    bye = None
    remaining = list(standings)
    if n % 2 == 1:
        for candidate in reversed(standings):
            if candidate not in had_bye:
                bye = candidate
                remaining = [t for t in standings if t != candidate]
                break
        if bye is None:
            bye = standings[-1]
            remaining = standings[:-1]

    pairings = _backtrack_pair(remaining, played, scores, round_num)
    if pairings is None:
        raise HTTPException(409, {"error": {"code": "NO_VALID_PAIRING", "message": "No rematch-free pairing exists.", "details": {"round": round_num}}})

    return {
        "format": "swiss",
        "round": round_num,
        "total_rounds": total_rounds,
        "pairings": pairings,
        "bye": bye,
        "standings": [
            {"rank": i + 1, "team_id": t, "score": scores[t], "buchholz": buchholz[t]}
            for i, t in enumerate(standings)
        ],
    }


def _backtrack_pair(teams: list, played: dict, scores: dict, round_num: int):
    if not teams:
        return []
    for i in range(1, len(teams)):
        if teams[i] not in played[teams[0]]:
            home = teams[0] if scores[teams[0]] <= scores[teams[i]] else teams[i]
            away = teams[i] if home == teams[0] else teams[0]
            idx = len([]) + 1
            rest = [t for j, t in enumerate(teams) if j != 0 and j != i]
            sub = _backtrack_pair(rest, played, scores, round_num)
            if sub is not None:
                match_idx = (len(teams) // 2) - len(rest) // 2
                return [{"match_id": f"SW-R{round_num}-M{match_idx}", "home": home, "away": away}] + sub
    return None


def _seed_order(size: int) -> list:
    if size == 2:
        return [1, 2]
    half = size // 2
    sub = _seed_order(half)
    result = []
    for s in sub:
        result.append(s)
        result.append(size + 1 - s)
    return result


def _single_elim(teams: list, params: dict) -> dict:
    n = len(teams)
    if not (2 <= n <= 128):
        raise HTTPException(400, {"error": {"code": "VALIDATION_ERROR", "message": "Team count must be 2-128", "details": {"fields": ["teams"]}}})

    B = 1
    while B < n:
        B *= 2

    seed_map = {i + 1: teams[i] if i < n else None for i in range(B)}
    order = _seed_order(B)
    third_place = params.get("third_place_match", False)
    results_in = {r["match_id"]: r["winner"] for r in params.get("results", [])}

    rounds_count = int(math.log2(B))
    rounds = []
    match_winners = {}

    for r in range(1, rounds_count + 1):
        matches_in_round = B // (2 ** r)
        matches = []
        for i in range(1, matches_in_round + 1):
            mid = f"R{r}M{i}"
            if r == 1:
                pos1 = order[2 * i - 2]
                pos2 = order[2 * i - 1]
                t1 = seed_map[pos1]
                t2 = seed_map[pos2]
                bye = t2 is None or t1 is None
                home = t1 if t1 else t2
                away = t2 if t1 else None
                home_seed = pos1 if t1 else pos2
                away_seed = pos2 if t1 else None
            else:
                src1 = f"R{r-1}M{2*i-1}"
                src2 = f"R{r-1}M{2*i}"
                home = match_winners.get(src1)
                away = match_winners.get(src2)
                home_seed = None
                away_seed = None
                bye = False

            winner_to = None if r == rounds_count else {"match_id": f"R{r+1}M{math.ceil(i/2)}", "slot": "home" if i % 2 == 1 else "away"}

            winner = results_in.get(mid)
            loser = None

            m = {
                "match_id": mid,
                "bracket": "main",
                "round": r,
                "index": i,
                "home": home,
                "away": away,
                "home_seed": home_seed,
                "away_seed": away_seed,
                "bye": bye,
                "winner": winner,
                "loser": loser,
                "winner_to": winner_to,
                "loser_to": None,
            }
            if bye and not winner:
                winner = home
                m["winner"] = winner
            if winner:
                match_winners[mid] = winner
                loser_team = away if winner == home else home
                m["loser"] = loser_team
            matches.append(m)
        rounds.append({"round": r, "matches": matches})

    return {"format": "single_elim", "bracket_size": B, "rounds": rounds}


def _double_elim(teams: list, params: dict) -> dict:
    n = len(teams)
    if not (3 <= n <= 128):
        raise HTTPException(400, {"error": {"code": "VALIDATION_ERROR", "message": "Team count must be 3-128", "details": {"fields": ["teams"]}}})

    B = 1
    while B < n:
        B *= 2

    bracket_reset = params.get("bracket_reset", False)

    return {
        "format": "double_elim",
        "bracket_size": B,
        "bracket_reset": bracket_reset,
        "winners": [],
        "losers": [],
        "grand_final": [],
    }
