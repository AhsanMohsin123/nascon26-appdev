"""Concurrency-safe merchandise store with mock payment gateway."""
import json
import base64
import hashlib
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.auth.jwt import sign_payload


DISCOUNT_CODES = {
    "WELCOME10": {"percent": 10},
}

MOCK_GATEWAY = {
    "tok_success": ("auth_success", "cap_success", "captured"),
    "tok_declined": None,
    "tok_capture_fail": ("auth_success", None, "capture_failed"),
}


async def checkout(db: AsyncSession, body: dict) -> dict:
    order_id = body.get("order_id")
    customer_id = body.get("customer_id")
    items = body.get("items", [])
    discount_code = body.get("discount_code")
    payment = body.get("payment", {})

    # Idempotency check
    existing = await db.execute(text("SELECT response FROM orders WHERE id = :id"), {"id": order_id})
    existing_row = existing.fetchone()
    if existing_row:
        return json.loads(existing_row[0])

    # Validate variants
    for item in items:
        vid = item["variant_id"]
        row = await db.execute(text("SELECT id FROM product_variants WHERE id = :id"), {"id": vid})
        if not row.fetchone():
            raise HTTPException(404, {"error": {"code": "VARIANT_NOT_FOUND", "message": f"Variant {vid} not found.", "details": {}}})

    # Validate discount
    discount_percent = 0
    if discount_code:
        if discount_code not in DISCOUNT_CODES:
            raise HTTPException(400, {"error": {"code": "INVALID_DISCOUNT_CODE", "message": f"Unknown discount code {discount_code}.", "details": {}}})
        discount_percent = DISCOUNT_CODES[discount_code]["percent"]

    # Atomic stock reservation using SELECT FOR UPDATE
    reserved = {}
    subtotal = 0
    item_details = []
    try:
        for item in items:
            vid = item["variant_id"]
            qty = item["quantity"]
            row = await db.execute(text("SELECT stock, price_minor FROM product_variants WHERE id = :id FOR UPDATE"), {"id": vid})
            r = row.fetchone()
            if not r or r[0] < qty:
                raise HTTPException(409, {"error": {"code": "OUT_OF_STOCK", "message": f"Variant {vid} has no stock left.", "details": {"variant_id": vid}}})
            reserved[vid] = qty
            subtotal += r[1] * qty
            item_details.append({"variant_id": vid, "quantity": qty, "unit_price_minor": r[1]})
            await db.execute(text("UPDATE product_variants SET stock = stock - :qty WHERE id = :id"), {"qty": qty, "id": vid})

        discount_minor = (subtotal * discount_percent) // 100
        total_minor = subtotal - discount_minor

        # Mock payment
        token = payment.get("token", "tok_success")
        if token == "tok_declined":
            raise HTTPException(402, {"error": {"code": "PAYMENT_DECLINED", "message": "Payment declined.", "details": {}}})

        gw = MOCK_GATEWAY.get(token, MOCK_GATEWAY["tok_success"])
        auth_id, cap_id, state = gw[0], gw[1], gw[2]

        if token == "tok_capture_fail":
            raise HTTPException(402, {"error": {"code": "PAYMENT_CAPTURE_FAILED", "message": "Payment capture failed.", "details": {}}})

        paid_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        receipt_payload = {
            "order_id": order_id,
            "customer_id": customer_id,
            "items": item_details,
            "subtotal_minor": subtotal,
            "discount_minor": discount_minor,
            "total_minor": total_minor,
            "currency": "PKR",
            "paid_at": paid_at,
        }

        sig = sign_payload(order_id, receipt_payload)
        total_major = total_minor / 100
        pdf_content = f"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n% Order: {order_id}\n% Total: PKR {total_major:.2f}\n%%EOF"
        pdf_b64 = base64.b64encode(pdf_content.encode()).decode()

        response = {
            "order_id": order_id,
            "status": "paid",
            "currency": "PKR",
            "items": item_details,
            "subtotal_minor": subtotal,
            "discount_minor": discount_minor,
            "total_minor": total_minor,
            "payment": {"authorization_id": auth_id, "capture_id": cap_id, "state": state},
            "receipt": {"payload": receipt_payload, "signature": sig, "pdf_base64": pdf_b64},
        }

        await db.execute(text(
            "INSERT INTO orders (id, customer_id, status, response) VALUES (:id, :cid, 'paid', :resp)"
        ), {"id": order_id, "cid": customer_id, "resp": json.dumps(response)})
        await db.commit()

        return response

    except HTTPException as e:
        await db.rollback()
        raise


async def get_inventory(db: AsyncSession, variant_id: str) -> dict:
    row = await db.execute(text("SELECT stock FROM product_variants WHERE id = :id"), {"id": variant_id})
    r = row.fetchone()
    if not r:
        raise HTTPException(404, {"error": {"code": "VARIANT_NOT_FOUND", "message": f"Variant {variant_id} not found.", "details": {}}})
    return {"variant_id": variant_id, "stock": r[0], "reserved": 0}
