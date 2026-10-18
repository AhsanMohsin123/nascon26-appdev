"""Stream key lifecycle — generate/rotate/revoke, signed with DAY2_SALT (Section 5.4)."""
import secrets
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.domain.signing import sign_day2

VALID_ACTIONS = {"generate", "rotate", "revoke"}


def _new_key() -> str:
    return "sk_live_" + secrets.token_hex(8)


def _ingest_endpoints(stream_key: str) -> dict:
    return {
        "rtmp": f"rtmp://localhost:1935/live/{stream_key}",
        "webrtc": f"http://localhost:8889/live/{stream_key}/whip",
    }


def _playback_url(stream_key: str) -> str:
    return f"http://localhost:8888/live/{stream_key}/index.m3u8"


async def manage_stream_key(db: AsyncSession, body: dict) -> tuple[int, dict]:
    action = body.get("action")
    player_id = body.get("player_id")
    label = body.get("label", "default")
    override = body.get("stream_key_override")

    if action not in VALID_ACTIONS:
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "action must be one of generate, rotate, revoke.", "details": {"fields": ["action"]}}})
    if not player_id or not isinstance(player_id, str):
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "player_id is required.", "details": {"fields": ["player_id"]}}})
    if not isinstance(label, str) or not (1 <= len(label) <= 64):
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "label must be 1-64 chars.", "details": {"fields": ["label"]}}})

    player_row = await db.execute(text("SELECT id FROM players WHERE id=:id"), {"id": player_id})
    if not player_row.fetchone():
        raise HTTPException(404, detail={"error": {"code": "PLAYER_NOT_FOUND", "message": f"Player {player_id} not found.", "details": {}}})

    existing = await db.execute(text("SELECT stream_key, status FROM stream_keys WHERE player_id=:pid"), {"pid": player_id})
    existing_row = existing.fetchone()

    if action == "revoke":
        if not existing_row or existing_row[1] != "active":
            raise HTTPException(404, detail={"error": {"code": "STREAM_NOT_FOUND", "message": f"No active stream key for player {player_id}.", "details": {}}})
        stream_key = existing_row[0]
        await db.execute(text("UPDATE stream_keys SET status='revoked' WHERE player_id=:pid"), {"pid": player_id})
        await db.commit()
        status = "revoked"
        sig_payload = {"action": action, "player_id": player_id, "status": status, "stream_key": stream_key}
        return 200, {
            "player_id": player_id,
            "label": label,
            "stream_key": stream_key,
            "status": status,
            "ingest_endpoints": None,
            "playback_url": None,
            "signature": sign_day2(stream_key, sig_payload),
        }

    # generate | rotate
    stream_key = override if override else _new_key()
    status = "active"
    if existing_row:
        await db.execute(text(
            "UPDATE stream_keys SET label=:label, stream_key=:sk, status='active' WHERE player_id=:pid"
        ), {"label": label, "sk": stream_key, "pid": player_id})
    else:
        await db.execute(text(
            "INSERT INTO stream_keys (player_id, label, stream_key, status) VALUES (:pid, :label, :sk, 'active')"
        ), {"pid": player_id, "label": label, "sk": stream_key})
    await db.commit()

    sig_payload = {"action": action, "player_id": player_id, "status": status, "stream_key": stream_key}
    response = {
        "player_id": player_id,
        "label": label,
        "stream_key": stream_key,
        "status": status,
        "ingest_endpoints": _ingest_endpoints(stream_key),
        "playback_url": _playback_url(stream_key),
        "signature": sign_day2(stream_key, sig_payload),
    }
    http_status = 201 if action == "generate" else 200
    return http_status, response
