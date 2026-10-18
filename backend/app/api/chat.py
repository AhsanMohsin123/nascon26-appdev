from fastapi import APIRouter, Request
from app.auth.middleware import reject_guest_write

router = APIRouter()


@router.post("/chat")
async def post_chat(body: dict, request: Request):
    """Minimal write endpoint — exists so the guest-boundary probe (Section 5.7) has a
    real target. Full moderation filtering lives in POST /audit/v1/moderation/test (5.8)."""
    reject_guest_write(request)
    return {"status": "accepted", "message_id": body.get("message_id")}
