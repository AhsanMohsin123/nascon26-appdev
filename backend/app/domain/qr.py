"""Dynamic cryptographic QR deep-linking (Section 5.6) — resolve, export, and scan telemetry."""
import io
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.domain.signing import sign_day2

BASE_URL = "http://localhost:8080"

_MATCH_ROUTE_BY_STATUS = {
    "upcoming": "/web/matches/{id}/preview",
    "in_progress": "/web/matches/{id}/live",
    "completed": "/web/matches/{id}/vod",
}
_MATCH_NOTICE_STATUSES = {"postponed", "cancelled", "abandoned"}


def _entity_type(entity_id: str) -> str:
    if entity_id.startswith("match-"):
        return "match"
    if entity_id.startswith("player-"):
        return "player"
    if entity_id.startswith("club-"):
        return "club"
    if entity_id.startswith("cs-session-"):
        return "costream"
    raise HTTPException(404, detail={"error": {"code": "QR_NOT_FOUND", "message": f"Unknown entity type for {entity_id}.", "details": {}}})


async def _target_route_and_status(db: AsyncSession, entity_id: str, entity_type: str) -> tuple[str, str | None]:
    if entity_type == "match":
        row = (await db.execute(text("SELECT status FROM matches WHERE id=:id"), {"id": entity_id})).fetchone()
        if not row:
            raise HTTPException(404, detail={"error": {"code": "QR_NOT_FOUND", "message": f"Match {entity_id} not found.", "details": {}}})
        status = row[0]
        if status in _MATCH_NOTICE_STATUSES:
            return f"/web/matches/{entity_id}/notice?state={status}", status
        template = _MATCH_ROUTE_BY_STATUS.get(status, _MATCH_ROUTE_BY_STATUS["upcoming"])
        return template.format(id=entity_id), status
    if entity_type == "player":
        row = (await db.execute(text("SELECT id FROM players WHERE id=:id"), {"id": entity_id})).fetchone()
        if not row:
            raise HTTPException(404, detail={"error": {"code": "QR_NOT_FOUND", "message": f"Player {entity_id} not found.", "details": {}}})
        return f"/web/players/{entity_id}", None
    if entity_type == "club":
        row = (await db.execute(text("SELECT id FROM clubs WHERE id=:id"), {"id": entity_id})).fetchone()
        if not row:
            raise HTTPException(404, detail={"error": {"code": "QR_NOT_FOUND", "message": f"Club {entity_id} not found.", "details": {}}})
        return f"/web/clubs/{entity_id}", None
    if entity_type == "costream":
        row = (await db.execute(text("SELECT session_id FROM costream_sessions WHERE session_id=:id"), {"id": entity_id})).fetchone()
        if not row:
            raise HTTPException(404, detail={"error": {"code": "QR_NOT_FOUND", "message": f"Co-stream session {entity_id} not found.", "details": {}}})
        return f"/web/costream/{entity_id}", None
    raise HTTPException(404, detail={"error": {"code": "QR_NOT_FOUND", "message": f"Unknown entity {entity_id}.", "details": {}}})


async def _ensure_mapping(db: AsyncSession, entity_id: str, entity_type: str) -> str:
    """Returns the short_code, creating a QR mapping on first resolution if the entity exists but has none seeded."""
    row = (await db.execute(text("SELECT short_code FROM qr_mappings WHERE entity_id=:id"), {"id": entity_id})).fetchone()
    if row:
        return row[0]
    short_code = entity_id
    await db.execute(text(
        "INSERT INTO qr_mappings (entity_id, entity_type, short_code, scan_count) VALUES (:eid, :etype, :code, 0) "
        "ON CONFLICT (entity_id) DO NOTHING"
    ), {"eid": entity_id, "etype": entity_type, "code": short_code})
    await db.commit()
    return short_code


def _device_family(user_agent: str | None) -> str:
    ua = (user_agent or "").lower()
    mobile_markers = ("mobi", "android", "iphone", "ipad")
    return "mobile" if any(m in ua for m in mobile_markers) else "desktop"


async def _record_scan(db: AsyncSession, entity_id: str, user_agent: str | None):
    """Privacy-safe telemetry only: aggregate device family + UTC hour bucket. No IP, no raw UA, no cookies (NFR-9)."""
    device_family = _device_family(user_agent)
    hour_bucket = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")
    await db.execute(text(
        "INSERT INTO qr_scan_telemetry (entity_id, device_family, hour_bucket, count) VALUES (:eid, :df, :hb, 1) "
        "ON CONFLICT (entity_id, device_family, hour_bucket) DO UPDATE SET count = qr_scan_telemetry.count + 1"
    ), {"eid": entity_id, "df": device_family, "hb": hour_bucket})
    await db.execute(text("UPDATE qr_mappings SET scan_count = scan_count + 1 WHERE entity_id=:id"), {"id": entity_id})
    await db.commit()


async def get_qr_metadata(db: AsyncSession, entity_id: str, inspect: bool, user_agent: str | None = None) -> dict:
    entity_type = _entity_type(entity_id)
    target_route, entity_status = await _target_route_and_status(db, entity_id, entity_type)
    short_code = await _ensure_mapping(db, entity_id, entity_type)

    if not inspect:
        await _record_scan(db, entity_id, user_agent)

    scan_row = (await db.execute(text("SELECT scan_count FROM qr_mappings WHERE entity_id=:id"), {"id": entity_id})).fetchone()
    scan_count = scan_row[0] if scan_row else 0

    short_url = f"{BASE_URL}/q/{short_code}"
    sig_payload = {"entity_id": entity_id, "short_url": short_url, "target_route": target_route}

    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "entity_status": entity_status,
        "short_url": short_url,
        "target_route": target_route,
        "deep_link_uri": f"nascon://entity/{entity_id}",
        "scan_count": scan_count,
        "export_formats": {
            "svg": f"{BASE_URL}/audit/v1/qr/{entity_id}/export.svg",
            "png": f"{BASE_URL}/audit/v1/qr/{entity_id}/export.png",
            "pdf": f"{BASE_URL}/audit/v1/qr/{entity_id}/export.pdf",
        },
        "signature": sign_day2(entity_id, sig_payload),
    }


async def resolve_short_code(db: AsyncSession, short_code: str, user_agent: str | None = None) -> str:
    """Returns the target_route to redirect to (302), recording a real scan."""
    row = (await db.execute(text("SELECT entity_id FROM qr_mappings WHERE short_code=:code"), {"code": short_code})).fetchone()
    if not row:
        raise HTTPException(404, detail={"error": {"code": "QR_NOT_FOUND", "message": f"Short code {short_code} not found.", "details": {}}})
    entity_id = row[0]
    entity_type = _entity_type(entity_id)
    target_route, _ = await _target_route_and_status(db, entity_id, entity_type)
    await _record_scan(db, entity_id, user_agent)
    return target_route


def _make_qr_png_bytes(data: str) -> bytes:
    import qrcode
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_qr_svg_str(data: str) -> str:
    import qrcode
    import qrcode.image.svg
    factory = qrcode.image.svg.SvgPathImage
    img = qrcode.make(data, image_factory=factory)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode("utf-8")


async def export_svg(db: AsyncSession, entity_id: str) -> str:
    meta = await get_qr_metadata(db, entity_id, inspect=True)
    return _make_qr_svg_str(meta["short_url"])


async def export_png(db: AsyncSession, entity_id: str) -> bytes:
    meta = await get_qr_metadata(db, entity_id, inspect=True)
    return _make_qr_png_bytes(meta["short_url"])


async def export_pdf(db: AsyncSession, entity_id: str) -> bytes:
    meta = await get_qr_metadata(db, entity_id, inspect=True)
    png_bytes = _make_qr_png_bytes(meta["short_url"])

    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "NaSCon '26 - Dynamic QR Poster", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, f"Entity: {entity_id}", ln=True)
    pdf.cell(0, 8, f"Short URL: {meta['short_url']}", ln=True)
    pdf.ln(5)
    pdf.image(io.BytesIO(png_bytes), x=70, y=pdf.get_y(), w=70)
    return bytes(pdf.output())
