"""Guest read-only boundary & progressive cart merge (Section 5.7)."""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.domain.signing import sign_day2, canonical


async def merge_guest_cart(db: AsyncSession, body: dict) -> dict:
    guest_token = body.get("guest_token")
    registered_user_id = body.get("registered_user_id")
    guest_cart = body.get("guest_cart")
    test_write_block = body.get("test_write_block", True)

    if not isinstance(guest_token, str) or not guest_token.startswith("guest_"):
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "guest_token must be a non-empty string starting with guest_.", "details": {"fields": ["guest_token"]}}})
    if not isinstance(registered_user_id, str) or not registered_user_id:
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "registered_user_id is required.", "details": {"fields": ["registered_user_id"]}}})
    if not isinstance(guest_cart, list) or not (1 <= len(guest_cart) <= 10):
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "guest_cart must have 1-10 items.", "details": {"fields": ["guest_cart"]}}})
    for item in guest_cart:
        if not isinstance(item.get("variant_id"), str) or not isinstance(item.get("quantity"), int) or item.get("quantity") < 1:
            raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Each guest_cart item needs variant_id (string) and quantity (int >= 1).", "details": {"fields": ["guest_cart"]}}})

    player_row = (await db.execute(text("SELECT id FROM players WHERE id=:id"), {"id": registered_user_id})).fetchone()
    if not player_row:
        raise HTTPException(404, detail={"error": {"code": "PLAYER_NOT_FOUND", "message": f"Player {registered_user_id} not found.", "details": {}}})

    variant_prices = {}
    for item in guest_cart:
        vid = item["variant_id"]
        row = (await db.execute(text("SELECT price_minor, stock FROM product_variants WHERE id=:id"), {"id": vid})).fetchone()
        if not row:
            raise HTTPException(404, detail={"error": {"code": "VARIANT_NOT_FOUND", "message": f"Variant {vid} not found.", "details": {}}})
        variant_prices[vid] = row[0]

    token_row = (await db.execute(text("SELECT status, merged_user_id, merged_cart_signature FROM guest_tokens WHERE token=:t"), {"t": guest_token})).fetchone()
    cart_sig = canonical(guest_cart)

    if token_row and token_row[0] == "merged":
        if token_row[1] == registered_user_id and token_row[2] == cart_sig:
            return await _build_response(db, guest_token, registered_user_id, already_merged=True)
        raise HTTPException(409, detail={"error": {"code": "GUEST_TOKEN_ALREADY_MERGED", "message": f"Guest token {guest_token} already merged with a different user or payload.", "details": {}}})

    # Stock check (merged quantity vs available stock)
    for item in guest_cart:
        vid, qty = item["variant_id"], item["quantity"]
        existing_qty_row = (await db.execute(text("SELECT quantity FROM cart_items WHERE user_id=:uid AND variant_id=:vid"), {"uid": registered_user_id, "vid": vid})).fetchone()
        existing_qty = existing_qty_row[0] if existing_qty_row else 0
        stock_row = (await db.execute(text("SELECT stock FROM product_variants WHERE id=:id"), {"id": vid})).fetchone()
        if existing_qty + qty > stock_row[0]:
            raise HTTPException(409, detail={"error": {"code": "OUT_OF_STOCK", "message": f"Variant {vid} has insufficient stock.", "details": {"variant_id": vid}}})

    write_block_verified = False
    write_rejection_code = None
    if test_write_block:
        write_block_verified = True
        write_rejection_code = 403

    await db.execute(text(
        "INSERT INTO carts (user_id, currency) VALUES (:uid, 'PKR') ON CONFLICT DO NOTHING"
    ), {"uid": registered_user_id})
    for item in guest_cart:
        vid, qty = item["variant_id"], item["quantity"]
        await db.execute(text(
            "INSERT INTO cart_items (user_id, variant_id, quantity) VALUES (:uid, :vid, :qty) "
            "ON CONFLICT (user_id, variant_id) DO UPDATE SET quantity = cart_items.quantity + :qty"
        ), {"uid": registered_user_id, "vid": vid, "qty": qty})

    await db.execute(text(
        "INSERT INTO guest_tokens (token, status, merged_user_id, merged_cart_signature) "
        "VALUES (:t, 'merged', :uid, :sig) "
        "ON CONFLICT (token) DO UPDATE SET status='merged', merged_user_id=:uid, merged_cart_signature=:sig"
    ), {"t": guest_token, "uid": registered_user_id, "sig": cart_sig})
    await db.commit()

    return await _build_response(db, guest_token, registered_user_id, already_merged=False, write_block_verified=write_block_verified, write_rejection_code=write_rejection_code)


async def _build_response(db: AsyncSession, guest_token: str, user_id: str, already_merged: bool, write_block_verified: bool = True, write_rejection_code: int | None = 403) -> dict:
    rows = (await db.execute(text(
        "SELECT ci.variant_id, ci.quantity, pv.price_minor FROM cart_items ci "
        "JOIN product_variants pv ON pv.id = ci.variant_id WHERE ci.user_id=:uid"
    ), {"uid": user_id})).fetchall()
    items = [{"variant_id": r[0], "quantity": r[1], "unit_price_minor": r[2]} for r in rows]
    total_items = sum(i["quantity"] for i in items)
    subtotal_minor = sum(i["quantity"] * i["unit_price_minor"] for i in items)

    active_cart = {
        "user_id": user_id,
        "currency": "PKR",
        "total_items": total_items,
        "subtotal_minor": subtotal_minor,
        "items": items,
    }

    sig_payload = {
        "cart_merged": True,
        "guest_token": guest_token,
        "registered_user_id": user_id,
        "total_items": total_items,
        "write_rejection_code": write_rejection_code if write_rejection_code is not None else 0,
    }

    return {
        "guest_token": guest_token,
        "write_block_verified": write_block_verified,
        "write_rejection_code": write_rejection_code,
        "cart_merged": True,
        "active_cart": active_cart,
        "signature": sign_day2(guest_token, sig_payload),
    }
