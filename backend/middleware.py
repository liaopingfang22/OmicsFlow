"""
Production middleware for OmicsFlow.
Includes request tracing, rate limiting, and global exception handling.
"""
import time
import uuid
import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("omicsflow.middleware")


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Adds request ID and timing to all requests."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        request.state.start_time = time.time()

        response = await call_next(request)

        duration_ms = (time.time() - request.state.start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

        status = response.status_code
        level = logging.WARNING if status >= 400 else logging.INFO
        logger.log(
            level,
            f"[{request_id}] {request.method} {request.url.path} → {status} ({duration_ms:.1f}ms)",
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter per IP address."""

    def __init__(self, app, requests_per_minute: int = 120):
        super().__init__(app)
        self.rpm = requests_per_minute
        self._requests: Dict[str, list] = defaultdict(list)
        self._request_count: int = 0
        self._cleanup_threshold: int = 100

    def _cleanup_expired(self):
        """Remove expired entries from all IPs to prevent memory leaks."""
        now = time.time()
        expired_ips = []
        for ip, timestamps in self._requests.items():
            self._requests[ip] = [t for t in timestamps if now - t < 60]
            if not self._requests[ip]:
                expired_ips.append(ip)
        for ip in expired_ips:
            del self._requests[ip]

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries for this client
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if now - t < 60
        ]

        # Periodic global cleanup every N requests to prevent memory leaks
        self._request_count += 1
        if self._request_count >= self._cleanup_threshold:
            self._request_count = 0
            self._cleanup_expired()

        if len(self._requests[client_ip]) >= self.rpm:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": "60"},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"[{request_id}] Unhandled exception: {type(exc).__name__}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": request_id,
        },
    )