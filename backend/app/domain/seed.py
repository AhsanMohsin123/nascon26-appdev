"""Seed / reset logic — wipes all state and recreates baseline data."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


BASELINE_SPORTS = [
    {
        "sport_id": "football",
        "name": "Football",
        "scoring_model": "event",
        "periods": {"count": 2, "duration_minutes": 45},
        "scoring_events": {"goal": {"points": 1}},
        "draw_allowed": True,
        "overtime": {"policy": "none"},
        "tie_break_order": ["h2h_points", "h2h_diff", "overall_diff", "scored", "fair_play", "draw_lots"],
        "roster": {"min_squad_size": 11, "max_squad_size": 25, "required_positions": {"gk": 1}},
    },
    {
        "sport_id": "basketball",
        "name": "Basketball",
        "scoring_model": "event",
        "periods": {"count": 4, "duration_minutes": 12},
        "scoring_events": {
            "free_throw": {"points": 1},
            "two_pointer": {"points": 2},
            "three_pointer": {"points": 3},
        },
        "draw_allowed": False,
        "overtime": {"policy": "extra_time", "duration_minutes": 5},
        "tie_break_order": ["h2h_points", "h2h_diff", "overall_diff", "scored", "fair_play", "draw_lots"],
        "roster": {"min_squad_size": 5, "max_squad_size": 15, "required_positions": {}},
    },
    {
        "sport_id": "cricket",
        "name": "Cricket",
        "scoring_model": "innings",
        "periods": {
            "innings_per_team": 1,
            "overs_per_innings": 20,
            "balls_per_over": 6,
            "wickets_per_innings": 10,
        },
        "scoring_events": {
            "dot_ball": {"runs": 0, "legal_ball": True, "wicket": False},
            "single": {"runs": 1, "legal_ball": True, "wicket": False},
            "two": {"runs": 2, "legal_ball": True, "wicket": False},
            "four": {"runs": 4, "legal_ball": True, "wicket": False},
            "six": {"runs": 6, "legal_ball": True, "wicket": False},
            "wide": {"runs": 1, "legal_ball": False, "wicket": False},
            "no_ball": {"runs": 1, "legal_ball": False, "wicket": False},
            "wicket": {"runs": 0, "legal_ball": True, "wicket": True},
        },
        "draw_allowed": True,
        "overtime": {"policy": "super_over"},
        "tie_break_order": ["h2h_points", "h2h_diff", "overall_diff", "scored", "fair_play", "draw_lots"],
        "roster": {"min_squad_size": 11, "max_squad_size": 18, "required_positions": {"wicketkeeper": 1}},
    },
    {
        "sport_id": "esports",
        "name": "Esports",
        "scoring_model": "round",
        "periods": {"best_of": 3},
        "scoring_events": {"round_win": {"rounds": 1}},
        "draw_allowed": False,
        "overtime": {"policy": "none"},
        "tie_break_order": ["h2h_points", "h2h_diff", "overall_diff", "scored", "fair_play", "draw_lots"],
        "roster": {"min_squad_size": 5, "max_squad_size": 8, "required_positions": {}},
    },
]


async def reset_and_seed(db: AsyncSession, seed: int, stock: dict):
    # Wipe all state
    tables = [
        "dlq_events", "moderation_actions", "chat_messages",
        "cart_items", "carts", "guest_tokens", "qr_mappings",
        "costream_sessions", "stream_keys",
        "offline_sync_actions", "orders", "product_variants", "products",
        "roster_audit", "player_registrations", "players", "squads", "clubs",
        "match_events", "matches", "league_teams", "leagues",
        "sports", "tenants", "users",
    ]
    for table in tables:
        try:
            await db.execute(text(f"DELETE FROM {table}"))
        except Exception:
            # A single missing/locked table must never abort the whole transaction and
            # silently skip wiping every table listed after it (real Day 1 bug: "order_items"
            # never existed, which poisoned this entire loop from "orders" onward).
            await db.rollback()
    await db.commit()

    # Seed tenants
    await db.execute(text(
        "INSERT INTO tenants (id, name) VALUES (:id, :name) ON CONFLICT DO NOTHING"
    ), [{"id": "tenant-alpha", "name": "Alpha Sports"}, {"id": "tenant-beta", "name": "Beta Athletics"}])

    # Seed sports
    import json
    for sport in BASELINE_SPORTS:
        await db.execute(text(
            "INSERT INTO sports (id, name, config) VALUES (:id, :name, :config) ON CONFLICT DO NOTHING"
        ), {"id": sport["sport_id"], "name": sport["name"], "config": json.dumps(sport)})

    # Seed product
    await db.execute(text(
        "INSERT INTO products (id, tenant_id, name) VALUES (:id, :tenant_id, :name) ON CONFLICT DO NOTHING"
    ), {"id": "prod-jersey-001", "tenant_id": "tenant-alpha", "name": "Jersey 001"})

    for variant_id, qty in stock.items():
        size = variant_id.split("-")[-1]
        await db.execute(text(
            "INSERT INTO product_variants (id, product_id, size, price_minor, currency, stock) "
            "VALUES (:id, :product_id, :size, :price, :currency, :stock) ON CONFLICT (id) DO UPDATE SET stock = :stock"
        ), {"id": variant_id, "product_id": "prod-jersey-001", "size": size,
            "price": 450000, "currency": "PKR", "stock": qty})

    # Seed RBAC scenario entities
    for league_id, tenant_id in [("league-alpha-1", "tenant-alpha"), ("league-alpha-2", "tenant-alpha"), ("league-beta-1", "tenant-beta")]:
        await db.execute(text(
            "INSERT INTO leagues (id, tenant_id, sport_id, config) VALUES (:id, :tenant_id, :sport_id, '{}') ON CONFLICT DO NOTHING"
        ), {"id": league_id, "tenant_id": tenant_id, "sport_id": "football"})

    for club_id, tenant_id in [("club-alpha-1", "tenant-alpha"), ("club-alpha-2", "tenant-alpha"), ("club-beta-1", "tenant-beta")]:
        await db.execute(text(
            "INSERT INTO clubs (id, tenant_id, name) VALUES (:id, :tenant_id, :name) ON CONFLICT DO NOTHING"
        ), {"id": club_id, "tenant_id": tenant_id, "name": club_id})

    for player_id, club_id in [("player-alpha-1", "club-alpha-1"), ("player-alpha-2", "club-alpha-2"), ("player-beta-1", "club-beta-1")]:
        await db.execute(text(
            "INSERT INTO players (id, club_id, name, position) VALUES (:id, :club_id, :name, 'gk') ON CONFLICT DO NOTHING"
        ), {"id": player_id, "club_id": club_id, "name": player_id})

    # Seed demo users (passwords are bcrypt hashes of "Nascon@26")
    from app.auth.jwt import hash_password
    import uuid
    pw = hash_password("Nascon@26")
    users = [
        (str(uuid.uuid4()), "admin@nascon.test", "super_admin", "tenant-alpha", None, None),
        (str(uuid.uuid4()), "organizer@nascon.test", "league_organizer", "tenant-alpha", "league-alpha-1", None),
        (str(uuid.uuid4()), "manager@nascon.test", "club_manager", "tenant-alpha", None, "club-alpha-1"),
        (str(uuid.uuid4()), "player@nascon.test", "player", "tenant-alpha", None, "club-alpha-1"),
        (str(uuid.uuid4()), "viewer@nascon.test", "viewer", "tenant-alpha", None, None),
    ]
    for uid, email, role, tenant_id, league_id, club_id in users:
        await db.execute(text(
            "INSERT INTO users (id, email, password_hash, role, tenant_id, league_id, club_id) "
            "VALUES (:id, :email, :pw, :role, :tenant_id, :league_id, :club_id) ON CONFLICT (email) DO UPDATE SET password_hash=:pw"
        ), {"id": uid, "email": email, "pw": pw, "role": role, "tenant_id": tenant_id, "league_id": league_id, "club_id": club_id})

    await db.commit()
    await _seed_day2_baseline(db)


async def _seed_day2_baseline(db: AsyncSession):
    """Phase II baseline seed — player-beta-2, match-m1 (1-0, in_progress), QR mappings,
    guest token guest_anon_tok_7721, and an empty cart for player-alpha-1."""
    import json
    from app.auth.jwt import sign_payload

    await db.execute(text(
        "INSERT INTO players (id, club_id, name, position) VALUES (:id, :club_id, :name, 'gk') ON CONFLICT DO NOTHING"
    ), {"id": "player-beta-2", "club_id": "club-beta-1", "name": "player-beta-2"})

    await db.execute(text(
        "INSERT INTO matches (id, league_id, sport_id, home_team_id, away_team_id, status) "
        "VALUES ('match-m1', 'league-alpha-1', 'football', 'club-alpha-1', 'club-alpha-2', 'in_progress') "
        "ON CONFLICT (id) DO UPDATE SET status = 'in_progress'"
    ))
    await db.execute(text("DELETE FROM match_events WHERE match_id = 'match-m1'"))
    goal_payload = {"team_id": "club-alpha-1", "event_type": "goal"}
    await db.execute(text(
        "INSERT INTO match_events (id, match_id, sequence, type, payload, signature) "
        "VALUES ('evt-seed-match-m1-goal', 'match-m1', 1, 'score', :payload, :sig)"
    ), {"payload": json.dumps(goal_payload), "sig": sign_payload("evt-seed-match-m1-goal", goal_payload)})

    qr_rows = [
        ("match-m1", "match", "m1-live"),
        ("player-alpha-1", "player", "p-alpha-1"),
        ("club-alpha-1", "club", "c-alpha-1"),
    ]
    for entity_id, entity_type, short_code in qr_rows:
        await db.execute(text(
            "INSERT INTO qr_mappings (entity_id, entity_type, short_code, scan_count) "
            "VALUES (:eid, :etype, :code, 0) ON CONFLICT (entity_id) DO UPDATE SET scan_count = 0"
        ), {"eid": entity_id, "etype": entity_type, "code": short_code})

    await db.execute(text(
        "INSERT INTO guest_tokens (token, status, merged_user_id, merged_cart_signature) "
        "VALUES ('guest_anon_tok_7721', 'valid', NULL, NULL) "
        "ON CONFLICT (token) DO UPDATE SET status = 'valid', merged_user_id = NULL, merged_cart_signature = NULL"
    ))

    await db.execute(text(
        "INSERT INTO carts (user_id, currency) VALUES ('player-alpha-1', 'PKR') ON CONFLICT DO NOTHING"
    ))
    await db.execute(text("DELETE FROM cart_items WHERE user_id = 'player-alpha-1'"))

    await db.commit()
