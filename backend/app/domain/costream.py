"""Synchronized 4-way co-stream orchestration & deterministic host-drop handoff (Section 5.5)."""
import json
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.domain.signing import sign_day2

VALID_LAYOUTS = {"solo", "grid_2", "grid_4", "spotlight"}


async def manage_session(db: AsyncSession, body: dict) -> tuple[int, dict]:
    session_id = body.get("session_id")
    host_player_id = body.get("host_player_id")
    participants = body.get("participants")
    layout = body.get("layout", "grid_4")
    simulate_host_drop = body.get("simulate_host_drop", False)

    if not isinstance(session_id, str) or not session_id:
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "session_id is required.", "details": {"fields": ["session_id"]}}})
    if not isinstance(host_player_id, str) or not host_player_id:
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "host_player_id is required.", "details": {"fields": ["host_player_id"]}}})
    if not isinstance(participants, list) or len(participants) == 0 or len(set(participants)) != len(participants):
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "participants must be a non-empty array of unique strings.", "details": {"fields": ["participants"]}}})
    if not isinstance(simulate_host_drop, bool):
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "simulate_host_drop must be a boolean.", "details": {"fields": ["simulate_host_drop"]}}})
    if layout not in VALID_LAYOUTS:
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": f"layout must be one of {sorted(VALID_LAYOUTS)}.", "details": {"fields": ["layout"]}}})

    for pid in set(participants) | {host_player_id}:
        row = (await db.execute(text("SELECT id FROM players WHERE id=:id"), {"id": pid})).fetchone()
        if not row:
            raise HTTPException(404, detail={"error": {"code": "PLAYER_NOT_FOUND", "message": f"Player {pid} not found.", "details": {}}})
    if host_player_id not in participants:
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "host_player_id must be an element of participants.", "details": {"fields": ["host_player_id"]}}})

    if len(participants) > 4:
        raise HTTPException(409, detail={"error": {"code": "COSTREAM_SESSION_FULL", "message": "Co-streaming supports at most 4 concurrent broadcasters.", "details": {}}})

    # Deterministic host-drop handoff
    if not simulate_host_drop:
        active_host = host_player_id
        handoff_occurred = False
        active_participants = list(participants)
        status = "active"
    elif len(participants) >= 2:
        remaining = [p for p in participants if p != host_player_id]
        active_host = remaining[0]
        handoff_occurred = True
        active_participants = remaining
        status = "active"
    else:
        active_host = None
        handoff_occurred = False
        active_participants = []
        status = "terminated"

    effective_count = len(active_participants)
    if layout == "solo" and effective_count > 1:
        raise HTTPException(400, detail={"error": {"code": "UNSUPPORTED_LAYOUT", "message": "Layout solo cannot fit active participant count.", "details": {}}})
    if layout == "grid_2" and effective_count > 2:
        raise HTTPException(400, detail={"error": {"code": "UNSUPPORTED_LAYOUT", "message": "Layout grid_2 cannot fit active participant count.", "details": {}}})

    chat_room_id = f"chat-{session_id}"
    participant_count = len(active_participants)

    existing = (await db.execute(text("SELECT session_id FROM costream_sessions WHERE session_id=:id"), {"id": session_id})).fetchone()
    http_status = 200 if existing else 201

    await db.execute(text(
        "INSERT INTO costream_sessions (session_id, host_player_id, active_host, participants, active_participants, layout, status, handoff_occurred, chat_room_id) "
        "VALUES (:sid, :host, :active_host, :participants, :active_participants, :layout, :status, :handoff, :chat_room_id) "
        "ON CONFLICT (session_id) DO UPDATE SET host_player_id=:host, active_host=:active_host, participants=:participants, "
        "active_participants=:active_participants, layout=:layout, status=:status, handoff_occurred=:handoff, chat_room_id=:chat_room_id"
    ), {
        "sid": session_id, "host": host_player_id, "active_host": active_host,
        "participants": json.dumps(participants), "active_participants": json.dumps(active_participants),
        "layout": layout, "status": status, "handoff": handoff_occurred, "chat_room_id": chat_room_id,
    })
    await db.commit()

    sig_payload = {
        "active_host": active_host, "handoff_occurred": handoff_occurred, "layout": layout,
        "participant_count": participant_count, "session_id": session_id, "status": status,
    }

    response = {
        "session_id": session_id,
        "status": status,
        "active_host": active_host,
        "handoff_occurred": handoff_occurred,
        "participant_count": participant_count,
        "active_participants": active_participants,
        "layout": layout,
        "composite_playback_url": f"http://localhost:8888/costream/{session_id}/index.m3u8",
        "chat_room_id": chat_room_id,
        "signature": sign_day2(session_id, sig_payload),
    }
    return http_status, response
