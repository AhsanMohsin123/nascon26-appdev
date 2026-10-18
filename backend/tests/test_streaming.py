import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/audit/v1/reset", json={})
        yield c


@pytest.mark.asyncio
async def test_generate_stream_key_201(client):
    r = await client.post("/audit/v1/stream/key", json={"action": "generate", "player_id": "player-alpha-1", "label": "OBS-Main-Desk"})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "active"
    assert body["stream_key"].startswith("sk_live_")
    assert body["ingest_endpoints"]["rtmp"].endswith(body["stream_key"])
    assert len(body["signature"]) == 64


@pytest.mark.asyncio
async def test_rotate_with_override_matches_appendix_a_message_format(client):
    r = await client.post("/audit/v1/stream/key", json={
        "action": "rotate", "player_id": "player-alpha-1", "stream_key_override": "sk_live_9f83a1b2c3d4e5f6",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["stream_key"] == "sk_live_9f83a1b2c3d4e5f6"
    assert body["status"] == "active"


@pytest.mark.asyncio
async def test_revoke_then_revoke_again_404(client):
    await client.post("/audit/v1/stream/key", json={"action": "generate", "player_id": "player-alpha-1"})
    r1 = await client.post("/audit/v1/stream/key", json={"action": "revoke", "player_id": "player-alpha-1"})
    assert r1.status_code == 200
    body = r1.json()
    assert body["status"] == "revoked"
    assert body["ingest_endpoints"] is None
    assert body["playback_url"] is None

    r2 = await client.post("/audit/v1/stream/key", json={"action": "revoke", "player_id": "player-alpha-1"})
    assert r2.status_code == 404
    assert r2.json()["error"]["code"] == "STREAM_NOT_FOUND"


@pytest.mark.asyncio
async def test_revoke_nonexistent_player_key_404(client):
    r = await client.post("/audit/v1/stream/key", json={"action": "revoke", "player_id": "player-alpha-2"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "STREAM_NOT_FOUND"


@pytest.mark.asyncio
async def test_unknown_player_404(client):
    r = await client.post("/audit/v1/stream/key", json={"action": "generate", "player_id": "nonexistent-player"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "PLAYER_NOT_FOUND"


@pytest.mark.asyncio
async def test_invalid_action_400(client):
    r = await client.post("/audit/v1/stream/key", json={"action": "bogus", "player_id": "player-alpha-1"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_missing_player_id_400(client):
    r = await client.post("/audit/v1/stream/key", json={"action": "generate"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_generate_again_replaces_existing_key(client):
    first = (await client.post("/audit/v1/stream/key", json={"action": "generate", "player_id": "player-alpha-1"})).json()
    second = (await client.post("/audit/v1/stream/key", json={"action": "generate", "player_id": "player-alpha-1"})).json()
    assert first["stream_key"] != second["stream_key"]
    assert second["status"] == "active"
