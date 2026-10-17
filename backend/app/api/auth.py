from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.auth.jwt import verify_password, create_access_token

router = APIRouter()


@router.post("/auth/login")
async def login(body: dict, db: AsyncSession = Depends(get_db)):
    email = body.get("email", "")
    password = body.get("password", "")

    row = await db.execute(text(
        "SELECT email, password_hash, role, tenant_id, league_id, club_id FROM users WHERE email=:email"
    ), {"email": email})
    user = row.fetchone()

    if not user or not verify_password(password, user[1]):
        raise HTTPException(401, detail={"error": {"code": "UNAUTHENTICATED", "message": "Invalid credentials.", "details": {}}})

    token_data = {
        "sub": user[0],
        "role": user[2],
        "tenant_id": user[3],
        "league_id": user[4],
        "club_id": user[5],
    }
    token = create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer", "role": user[2]}
