import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from app.core.config import settings

_requests: dict[str, deque[float]] = defaultdict(deque)


async def rate_limit_chat(request: Request) -> None:
    """Per-IP sliding-window limiter for POST /api/chat.

    In-memory and single-process — fine for this app's dev/demo deployment
    (one uvicorn worker), but won't coordinate across multiple workers or
    processes. Swap for a shared store (e.g. Redis) before running more than
    one worker. Exists to stop one client (or a runaway frontend retry loop)
    from burning through NVIDIA API quota, not as a security boundary.
    """
    if settings.chat_rate_limit_per_minute <= 0:
        return

    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window = _requests[client_ip]

    while window and now - window[0] > 60:
        window.popleft()

    if len(window) >= settings.chat_rate_limit_per_minute:
        retry_after = max(1, int(60 - (now - window[0])))
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests — try again in {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )

    window.append(now)
