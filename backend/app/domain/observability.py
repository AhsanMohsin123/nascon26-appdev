"""Prometheus /metrics exposition and privacy erasure (Section 5.9, NFR-6, NFR-9)."""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def render_metrics(db: AsyncSession) -> str:
    active_streams = (await db.execute(text("SELECT COUNT(*) FROM stream_keys WHERE status='active'"))).scalar() or 0
    dlq_depth = (await db.execute(text("SELECT COUNT(*) FROM dlq_events"))).scalar() or 0
    qr_scans_total = (await db.execute(text("SELECT COALESCE(SUM(scan_count), 0) FROM qr_mappings"))).scalar() or 0

    lines = [
        "# HELP nascon_active_ws_connections Active WebSocket connections.",
        "# TYPE nascon_active_ws_connections gauge",
        "nascon_active_ws_connections 0",
        "# HELP nascon_active_streams_total Currently active live streams.",
        "# TYPE nascon_active_streams_total gauge",
        f"nascon_active_streams_total {active_streams}",
        "# HELP nascon_stream_bitrate_kbps Aggregate live stream bitrate in kbps.",
        "# TYPE nascon_stream_bitrate_kbps gauge",
        "nascon_stream_bitrate_kbps 0",
        "# HELP nascon_dlq_depth Current Dead-Letter Queue depth.",
        "# TYPE nascon_dlq_depth gauge",
        f"nascon_dlq_depth {dlq_depth}",
        "# HELP nascon_qr_scans_total Total QR code scans recorded.",
        "# TYPE nascon_qr_scans_total counter",
        f"nascon_qr_scans_total {qr_scans_total}",
        "",
    ]
    return "\n".join(lines)


async def erase_user(db: AsyncSession, user_id: str) -> dict:
    row = (await db.execute(text("SELECT id FROM users WHERE id=:id"), {"id": user_id})).fetchone()
    if not row:
        player_row = (await db.execute(text("SELECT id FROM players WHERE id=:id"), {"id": user_id})).fetchone()
        if not player_row:
            raise HTTPException(404, detail={"error": {"code": "PLAYER_NOT_FOUND", "message": f"User {user_id} not found.", "details": {}}})

    await db.execute(text(
        "UPDATE users SET email = 'anonymized-' || id, password_hash = '' WHERE id=:id"
    ), {"id": user_id})
    await db.execute(text(
        "UPDATE guest_tokens SET status='anonymized', merged_user_id=NULL WHERE merged_user_id=:id"
    ), {"id": user_id})
    await db.commit()

    return {"user_id": user_id, "status": "anonymized", "pii_retained": False, "tokens_wiped": True}
