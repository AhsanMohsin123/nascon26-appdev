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
async def test_qr_match_in_progress_resolves_live(client):
    r = await client.get("/audit/v1/qr/match-m1?inspect=true")
    assert r.status_code == 200
    body = r.json()
    assert body["target_route"] == "/web/matches/match-m1/live"
    assert body["short_url"] == "http://localhost:8080/q/m1-live"
    assert len(body["signature"]) == 64


@pytest.mark.asyncio
async def test_qr_player_and_club_routes(client):
    r = await client.get("/audit/v1/qr/player-alpha-1?inspect=true")
    assert r.json()["target_route"] == "/web/players/player-alpha-1"

    r = await client.get("/audit/v1/qr/club-alpha-1?inspect=true")
    assert r.json()["target_route"] == "/web/clubs/club-alpha-1"


@pytest.mark.asyncio
async def test_qr_unknown_entity_404(client):
    r = await client.get("/audit/v1/qr/match-nope?inspect=true")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "QR_NOT_FOUND"


@pytest.mark.asyncio
async def test_short_code_redirect(client):
    r = await client.get("/q/m1-live", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/web/matches/match-m1/live"


@pytest.mark.asyncio
async def test_short_code_unknown_404(client):
    r = await client.get("/q/does-not-exist", follow_redirects=False)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "QR_NOT_FOUND"


@pytest.mark.asyncio
async def test_qr_target_mutates_after_match_completes_same_short_url(client):
    before = (await client.get("/audit/v1/qr/match-m1?inspect=true")).json()
    assert before["target_route"] == "/web/matches/match-m1/live"

    r = await client.post("/audit/v1/events", json={"event_id": "evt-qr-test-end", "match_id": "match-m1", "type": "match_end", "payload": {}})
    assert r.status_code == 200

    after = (await client.get("/audit/v1/qr/match-m1?inspect=true")).json()
    assert after["short_url"] == before["short_url"]
    assert after["target_route"] == "/web/matches/match-m1/vod"
    assert after["signature"] != before["signature"]


@pytest.mark.asyncio
async def test_scan_count_increments_on_real_scan_not_inspect(client):
    before = (await client.get("/audit/v1/qr/match-m1?inspect=true")).json()["scan_count"]
    await client.get("/audit/v1/qr/match-m1")  # real scan, no inspect
    after = (await client.get("/audit/v1/qr/match-m1?inspect=true")).json()["scan_count"]
    assert after == before + 1


@pytest.mark.asyncio
async def test_qr_exports_have_correct_content_type_and_magic_bytes(client):
    svg = await client.get("/audit/v1/qr/match-m1/export.svg")
    assert svg.status_code == 200
    assert svg.headers["content-type"] == "image/svg+xml"
    assert svg.text.startswith("<?xml") or svg.text.startswith("<svg")

    png = await client.get("/audit/v1/qr/match-m1/export.png")
    assert png.status_code == 200
    assert png.headers["content-type"] == "image/png"
    assert png.content[:8] == b"\x89PNG\r\n\x1a\n"

    pdf = await client.get("/audit/v1/qr/match-m1/export.pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content[:5] == b"%PDF-"


@pytest.mark.asyncio
async def test_costream_entity_not_found_before_session_exists(client):
    r = await client.get("/audit/v1/qr/cs-session-nope?inspect=true")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "QR_NOT_FOUND"
