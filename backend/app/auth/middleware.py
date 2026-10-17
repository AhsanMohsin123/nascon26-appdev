from fastapi import HTTPException, Request
from app.auth.jwt import decode_token
from jose import JWTError


async def require_auth(request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, {"error": {"code": "UNAUTHENTICATED", "message": "Missing token.", "details": {}}})
    try:
        return decode_token(auth[7:])
    except JWTError:
        raise HTTPException(401, {"error": {"code": "UNAUTHENTICATED", "message": "Invalid or expired token.", "details": {}}})
