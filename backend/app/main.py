import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.database import init_db
from app.api import health, reset, sports, fixtures, leagues, events, standings, roster, store, rbac, offline_sync, ping, streaming, qr, guest, chat, costream, moderation, observability, web, auth as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="NaSCon 26 — Sports League Platform", lifespan=lifespan)


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 1_048_576:
        return JSONResponse(status_code=413, content={"error": {"code": "PAYLOAD_TOO_LARGE", "message": "Request body exceeds 1 MB.", "details": {}}})
    return await call_next(request)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Overrides FastAPI's default handler, which wraps content in {"detail": ...} —
    # the spec's Standard Error Envelope requires the bare {"error": {...}} shape.
    content = exc.detail if isinstance(exc.detail, dict) and "error" in exc.detail else {
        "error": {"code": "ERROR", "message": str(exc.detail), "details": {}}
    }
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": str(exc), "details": {}}})


app.include_router(health.router)
app.include_router(auth_router.router)
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
app.include_router(streaming.router, prefix="/audit/v1")
app.include_router(qr.router, prefix="/audit/v1")
app.include_router(qr.public_router)
app.include_router(guest.router, prefix="/audit/v1")
app.include_router(costream.router, prefix="/audit/v1")
app.include_router(moderation.router, prefix="/audit/v1")
app.include_router(observability.audit_router, prefix="/audit/v1")
app.include_router(observability.router)
app.include_router(ping.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(web.router)
