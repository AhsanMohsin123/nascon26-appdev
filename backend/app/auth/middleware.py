from fastapi import HTTPException, Request
from app.auth.jwt import decode_token
from jose import JWTError


def reject_guest_write(request: Request):
    """Blocks any guest_anon_tok_* bearer token from reaching a write endpoint (403 GUEST_WRITE_FORBIDDEN)."""
    auth = request.headers.get("authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else None
    if token and token.startswith("guest_"):
        raise HTTPException(403, {"error": {"code": "GUEST_WRITE_FORBIDDEN", "message": "Anonymous guest tokens cannot perform write mutations.", "details": {"guest_token": token}}})


async def require_auth(request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, {"error": {"code": "UNAUTHENTICATED", "message": "Missing token.", "details": {}}})
    try:
        return decode_token(auth[7:])
    except JWTError:
        raise HTTPException(401, {"error": {"code": "UNAUTHENTICATED", "message": "Invalid or expired token.", "details": {}}})
