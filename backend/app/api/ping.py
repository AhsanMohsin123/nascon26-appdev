from fastapi import APIRouter, Request, Response
from app.domain import rate_limiter

router = APIRouter()


@router.get("/ping")
async def ping(request: Request, response: Response):
    await rate_limiter.check(request, response)
    return {"pong": True}
