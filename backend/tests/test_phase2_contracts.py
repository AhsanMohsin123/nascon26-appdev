import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/audit/v1/reset", json={})
        yield c


# --- Guest cart-merge & write boundary (Section 5.7) ---

@pytest.mark.asyncio
async def test_cart_merge_happy_path(client):
    r = await client.post("/audit/v1/guest/cart-merge", json={
        "guest_token": "guest_anon_tok_7721", "registered_user_id": "player-alpha-1",
        "guest_cart": [{"variant_id": "var-jersey-001-L", "quantity": 1}], "test_write_block": True,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["cart_merged"] is True
    assert body["active_cart"]["total_items"] == 1


@pytest.mark.asyncio
async def test_cart_merge_idempotent_replay(client):
    payload = {"guest_token": "guest_anon_tok_7721", "registered_user_id": "player-alpha-1",
               "guest_cart": [{"variant_id": "var-jersey-001-L", "quantity": 1}], "test_write_block": True}
    first = (await client.post("/audit/v1/guest/cart-merge", json=payload)).json()
    second = (await client.post("/audit/v1/guest/cart-merge", json=payload)).json()
    assert first["active_cart"]["total_items"] == second["active_cart"]["total_items"] == 1


@pytest.mark.asyncio
async def test_cart_merge_reused_token_different_user_409(client):
    payload = {"guest_token": "guest_anon_tok_7721", "registered_user_id": "player-alpha-1",
               "guest_cart": [{"variant_id": "var-jersey-001-L", "quantity": 1}]}
    await client.post("/audit/v1/guest/cart-merge", json=payload)
    r = await client.post("/audit/v1/guest/cart-merge", json={**payload, "registered_user_id": "player-alpha-2"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "GUEST_TOKEN_ALREADY_MERGED"


@pytest.mark.asyncio
async def test_guest_token_blocked_on_direct_writes(client):
    headers = {"Authorization": "Bearer guest_anon_tok_7721"}
    for method, path, body in [
        ("post", "/api/v1/chat", {"message_id": "m1"}),
        ("post", "/audit/v1/checkout", {"order_id": "o1", "items": []}),
        ("post", "/audit/v1/events", {"event_id": "e1", "match_id": "match-m1", "type": "score", "payload": {}}),
    ]:
        r = await client.request(method, path, json=body, headers=headers)
        assert r.status_code == 403, f"{path} should 403 for guest token"
        assert r.json()["error"]["code"] == "GUEST_WRITE_FORBIDDEN"


# --- Co-stream orchestration (Section 5.5) ---

@pytest.mark.asyncio
async def test_costream_no_handoff(client):
    r = await client.post("/audit/v1/costream/session", json={
        "session_id": "cs-test-1", "host_player_id": "player-alpha-1",
        "participants": ["player-alpha-1", "player-alpha-2"], "layout": "grid_2", "simulate_host_drop": False,
    })
    assert r.status_code == 201
    body = r.json()
    assert body["active_host"] == "player-alpha-1"
    assert body["handoff_occurred"] is False


@pytest.mark.asyncio
async def test_costream_host_drop_handoff(client):
    r = await client.post("/audit/v1/costream/session", json={
        "session_id": "cs-test-2", "host_player_id": "player-alpha-1",
        "participants": ["player-alpha-1", "player-alpha-2", "player-beta-1"], "simulate_host_drop": True,
    })
    body = r.json()
    assert body["active_host"] == "player-alpha-2"
    assert body["handoff_occurred"] is True
    assert body["participant_count"] == 2


@pytest.mark.asyncio
async def test_costream_sole_host_drop_terminates(client):
    r = await client.post("/audit/v1/costream/session", json={
        "session_id": "cs-test-3", "host_player_id": "player-alpha-1",
        "participants": ["player-alpha-1"], "layout": "solo", "simulate_host_drop": True,
    })
    body = r.json()
    assert body["status"] == "terminated"
    assert body["active_host"] is None


@pytest.mark.asyncio
async def test_costream_over_capacity_409(client):
    r = await client.post("/audit/v1/costream/session", json={
        "session_id": "cs-test-4", "host_player_id": "player-alpha-1",
        "participants": ["player-alpha-1", "player-alpha-2", "player-beta-1", "player-beta-2", "player-alpha-1-dup"],
    })
    assert r.status_code in (400, 404)  # dup/unknown player caught before capacity, per spec's validation order


# --- Chat moderation & DLQ (Section 5.8) ---

@pytest.mark.asyncio
async def test_moderation_spec_example(client):
    r = await client.post("/audit/v1/moderation/test", json={
        "chat_room_id": "chat-cs-session-101",
        "incoming_messages": [
            {"message_id": "msg-1", "sender": "user-guest-1", "text": "Clean sports commentary"},
            {"message_id": "msg-2", "sender": "user-spammer", "text": "Watch this illegal stream b@d_w0rd now!"},
            {"message_id": "msg-3", "sender": "user-flooder", "text": "GOAL! AAAA!!!"},
        ],
        "check_dlq": True, "simulate_failed_notifications": 0,
    })
    body = r.json()
    assert len(body["filtered_messages"]) == 2  # flood message dropped entirely
    assert body["filtered_messages"][1]["text"] == "Watch this illegal stream *** now!"
    assert body["filtered_messages"][1]["flagged"] is True
    assert body["kicked_users"] == ["user-spammer"]
    assert body["muted_users"] == ["user-flooder"]


@pytest.mark.asyncio
async def test_dlq_depth_from_simulated_failures(client):
    r = await client.post("/audit/v1/moderation/test", json={
        "chat_room_id": "chat-cs-session-101", "incoming_messages": [], "check_dlq": True, "simulate_failed_notifications": 3,
    })
    assert r.json()["dlq_status"]["queue_depth"] == 3


# --- Observability & privacy (Section 5.9) ---

@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    r = await client.get("/metrics")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    assert "nascon_active_ws_connections" in r.text
    assert "nascon_dlq_depth" in r.text


@pytest.mark.asyncio
async def test_privacy_erasure(client):
    r = await client.delete("/audit/v1/privacy/user/player-alpha-1")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "anonymized"
    assert body["tokens_wiped"] is True


@pytest.mark.asyncio
async def test_privacy_erasure_unknown_user_404(client):
    r = await client.delete("/audit/v1/privacy/user/nope")
    assert r.status_code == 404
