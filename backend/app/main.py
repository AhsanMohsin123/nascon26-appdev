import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import init_db
from app.api import health, reset, sports, fixtures, leagues, events, standings, roster, store, rbac, offline_sync, ping


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="NaSCon 26 — Sports League Platform", lifespan=lifespan)


@app.exception_handler(413)
async def payload_too_large(request: Request, exc):
    return JSONResponse(status_code=413, content={"error": {"code": "PAYLOAD_TOO_LARGE", "message": "Request body exceeds 1 MB.", "details": {}}})


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 1_048_576:
        return JSONResponse(status_code=413, content={"error": {"code": "PAYLOAD_TOO_LARGE", "message": "Request body exceeds 1 MB.", "details": {}}})
    return await call_next(request)


app.include_router(health.router)
app.include_router(reset.router, prefix="/audit/v1")
app.include_router(sports.router, prefix="/audit/v1")
app.include_router(fixtures.router, prefix="/audit/v1")
app.include_router(leagues.router, prefix="/audit/v1")
app.include_router(events.router, prefix="/audit/v1")
app.include_router(standings.router, prefix="/audit/v1")
app.include_router(roster.router, prefix="/audit/v1")
app.include_router(store.router, prefix="/audit/v1")
app.include_router(rbac.router, prefix="/audit/v1")
app.include_router(offline_sync.router, prefix="/audit/v1")
app.include_router(ping.router, prefix="/api/v1")
