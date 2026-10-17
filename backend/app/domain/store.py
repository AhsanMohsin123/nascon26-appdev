"""Concurrency-safe merchandise store — SELECT FOR UPDATE prevents overselling."""
import json, base64
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.auth.jwt import sign_payload, canonical_json


DISCOUNT_CODES = {"WELCOME10": 10}


async def checkout(db: AsyncSession, body: dict) -> dict:
    order_id = body.get("order_id")
    customer_id = body.get("customer_id")
    items = body.get("items", [])
    discount_code = body.get("discount_code")
    payment = body.get("payment", {})

    if not order_id:
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "order_id required", "details": {"fields": ["order_id"]}}})

    # Idempotency
    existing = await db.execute(text("SELECT response FROM orders WHERE id=:id"), {"id": order_id})
    row = existing.fetchone()
    if row:
        stored = json.loads(row[0])
        # Check for different body (DUPLICATE_ORDER_ID)
        if stored.get("_order_body_hash") and stored["_order_body_hash"] != _body_hash(body):
            raise HTTPException(409, detail={"error": {"code": "DUPLICATE_ORDER_ID", "message": f"Order {order_id} reused with different body.", "details": {}}})
        return {k: v for k, v in stored.items() if k != "_order_body_hash"}

    # 1. Validate schema
    if not items:
        raise HTTPException(400, detail={"error": {"code": "VALIDATION_ERROR", "message": "items required", "details": {"fields": ["items"]}}})

    # 2. Check variants exist
    for item in items:
        vid = item.get("variant_id")
        r = await db.execute(text("SELECT id FROM product_variants WHERE id=:id"), {"id": vid})
        if not r.fetchone():
            raise HTTPException(404, detail={"error": {"code": "VARIANT_NOT_FOUND", "message": f"Variant {vid} not found.", "details": {}}})

    # 3. Validate discount
    discount_percent = 0
    if discount_code:
        if discount_code not in DISCOUNT_CODES:
            raise HTTPException(400, detail={"error": {"code": "INVALID_DISCOUNT_CODE", "message": f"Unknown discount code {discount_code}.", "details": {}}})
        discount_percent = DISCOUNT_CODES[discount_code]

    # 4. Atomic reserve — SELECT FOR UPDATE
    subtotal = 0
    item_details = []
    try:
        for item in items:
            vid = item["variant_id"]
            qty = item.get("quantity", 1)
            r = await db.execute(text(
                "SELECT stock, price_minor FROM product_variants WHERE id=:id FOR UPDATE"
            ), {"id": vid})
            row2 = r.fetchone()
            if not row2 or row2[0] < qty:
                await db.rollback()
                raise HTTPException(409, detail={"error": {"code": "OUT_OF_STOCK", "message": f"Variant {vid} has no stock left.", "details": {"variant_id": vid}}})
            await db.execute(text("UPDATE product_variants SET stock=stock-:qty WHERE id=:id"), {"qty": qty, "id": vid})
            subtotal += row2[1] * qty
            item_details.append({"variant_id": vid, "quantity": qty, "unit_price_minor": row2[1]})

        # 5. Mock payment
        token = payment.get("token", "tok_success")
        if token == "tok_declined":
            await db.rollback()
            raise HTTPException(402, detail={"error": {"code": "PAYMENT_DECLINED", "message": "Payment declined.", "details": {}}})

        auth_id = "auth_" + order_id[-6:]
        cap_id = "cap_" + order_id[-6:]

        if token == "tok_capture_fail":
            await db.rollback()
            raise HTTPException(402, detail={"error": {"code": "PAYMENT_CAPTURE_FAILED", "message": "Payment capture failed.", "details": {}}})

        discount_minor = (subtotal * discount_percent) // 100
        total_minor = subtotal - discount_minor
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
        pdf_content = _generate_pdf(order_id, total_major, receipt_payload)
        pdf_b64 = base64.b64encode(pdf_content).decode()

        response = {
            "order_id": order_id,
            "status": "paid",
            "currency": "PKR",
            "items": item_details,
            "subtotal_minor": subtotal,
            "discount_minor": discount_minor,
            "total_minor": total_minor,
            "payment": {"authorization_id": auth_id, "capture_id": cap_id, "state": "captured"},
            "receipt": {"payload": receipt_payload, "signature": sig, "pdf_base64": pdf_b64},
            "_order_body_hash": _body_hash(body),
        }

        await db.execute(text(
            "INSERT INTO orders (id, customer_id, status, response) VALUES (:id, :cid, 'paid', :resp)"
        ), {"id": order_id, "cid": customer_id, "resp": json.dumps(response)})
        await db.commit()

        return {k: v for k, v in response.items() if k != "_order_body_hash"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, detail={"error": {"code": "INTERNAL_ERROR", "message": str(e), "details": {}}})


def _body_hash(body: dict) -> str:
    import hashlib
    return hashlib.sha256(canonical_json(body).encode()).hexdigest()


def _generate_pdf(order_id: str, total_major: float, payload: dict) -> bytes:
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "NaSCon '26 — Order Receipt", ln=True, align="C")
        pdf.ln(5)
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 8, f"Order ID: {order_id}", ln=True)
        pdf.cell(0, 8, f"Customer: {payload.get('customer_id', '')}", ln=True)
        pdf.cell(0, 8, f"Paid at: {payload.get('paid_at', '')}", ln=True)
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Items:", ln=True)
        pdf.set_font("Helvetica", size=11)
        for item in payload.get("items", []):
            price = item["unit_price_minor"] / 100
            pdf.cell(0, 7, f"  {item['variant_id']}  x{item['quantity']}  @ PKR {price:.2f}", ln=True)
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, f"Total: PKR {total_major:.2f}", ln=True)
        return pdf.output()
    except Exception:
        # Fallback minimal PDF
        content = f"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj 4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj 5 0 obj\n<</Length 60>>\nstream\nBT /F1 12 Tf 50 750 Td ({order_id}) Tj 0 -20 Td (PKR {total_major:.2f}) Tj ET\nendstream\nendobj\nxref\n0 6\ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n0\n%%EOF"
        return content.encode("latin-1")


async def get_inventory(db: AsyncSession, variant_id: str) -> dict:
    r = await db.execute(text("SELECT stock FROM product_variants WHERE id=:id"), {"id": variant_id})
    row = r.fetchone()
    if not row:
        raise HTTPException(404, detail={"error": {"code": "VARIANT_NOT_FOUND", "message": f"Variant {variant_id} not found.", "details": {}}})
    return {"variant_id": variant_id, "stock": row[0], "reserved": 0}
