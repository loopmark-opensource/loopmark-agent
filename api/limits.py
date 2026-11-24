"""
Request limits for the REST API (issue #70): body size cap and per-client rate limits.

Defaults suit one self-hosted team; override with environment variables:

    LOOPMARK_API_MAX_BODY_BYTES   max request body, default 1_000_000 (413 above it)
    LOOPMARK_API_CHAT_PER_MIN     POST /chat requests per client per minute, default 20
    LOOPMARK_API_ANALYZE_PER_MIN  POST /analyze/website per client per minute, default 10
"""

from __future__ import annotations

import hashlib
import math
import os
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MAX_BODY_ENV = "LOOPMARK_API_MAX_BODY_BYTES"
CHAT_RATE_ENV = "LOOPMARK_API_CHAT_PER_MIN"
ANALYZE_RATE_ENV = "LOOPMARK_API_ANALYZE_PER_MIN"

DEFAULT_MAX_BODY = 1_000_000
DEFAULT_CHAT_PER_MIN = 20
DEFAULT_ANALYZE_PER_MIN = 10


def env_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, ""))
    except ValueError:
        return default
    return value if value > 0 else default


class BodySizeLimitMiddleware:
    """
    Reject bodies over `max_bytes` with 413.

    The body is read here (never more than `max_bytes` + one chunk) and replayed to the app,
    so chunked uploads without Content-Length are caught too.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        declared = headers.get(b"content-length")
        if declared is not None and declared.isdigit() and int(declared) > self.max_bytes:
            await self._reject(send)
            return

        chunks: list[bytes] = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body = message.get("body", b"")
            size += len(body)
            if size > self.max_bytes:
                await self._reject(send)
                return
            chunks.append(body)
            if not message.get("more_body", False):
                break

        replayed = False

        async def replay() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)

    async def _reject(self, send: Send) -> None:
        body = b'{"detail":"Request body too large (limit %d bytes)."}' % self.max_bytes
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
            }
        )
        await send({"type": "http.response.body", "body": body})


class RateLimiter:
    """In-memory sliding-window limiter. Per process: run one worker, or put a proxy limit in front."""

    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, client: str) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[client]
            while hits and now - hits[0] >= self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                retry_after = max(1, math.ceil(self.window - (now - hits[0])))
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded ({self.limit} requests per {int(self.window)}s).",
                    headers={"Retry-After": str(retry_after)},
                )
            hits.append(now)


def client_key(request: Request) -> str:
    """Bucket by API key when one is sent (hashed, never stored raw), otherwise by client IP."""
    api_key = request.headers.get("x-api-key")
    if api_key:
        return "key:" + hashlib.sha256(api_key.encode()).hexdigest()[:16]
    return "ip:" + (request.client.host if request.client else "unknown")


def rate_limit(limiter: RateLimiter):
    def dependency(request: Request) -> None:
        limiter.check(client_key(request))

    return dependency
