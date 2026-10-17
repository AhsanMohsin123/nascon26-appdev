"""Rate limiting for /api/v1/* — 100 req per 10s rolling window per IP."""
import time
from fastapi import HTTPException, Request, Response
from collections import defaultdict

_window: dict = defaultdict(list)
LIMIT = 100
WINDOW_SECONDS = 10


async def check(request: Request, response: Response):
    ip = request.client.host
    now = time.time()
    window_start = now - WINDOW_SECONDS

    _window[ip] = [t for t in _window[ip] if t > window_start]

    if len(_window[ip]) >= LIMIT:
        response.headers["Retry-After"] = str(WINDOW_SECONDS)
        raise HTTPException(429, {"error": {"code": "RATE_LIMITED", "message": "Rate limit exceeded.", "details": {}}})

    _window[ip].append(now)
