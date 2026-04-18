"""
Production middleware stack for Teluka.

Applied in order (outermost = first to receive request, last to send response):
  1. RequestLoggingMiddleware  — log every request with timing + status
  2. SecurityHeadersMiddleware — attach hardened HTTP security headers
  3. RateLimitMiddleware       — per-IP sliding-window rate limiter
  4. GZipMiddleware            — compress text responses ≥ 1 KB
  5. TrustedHostMiddleware     — reject requests with unexpected Host header (prod)
  6. HTTPSRedirectMiddleware   — redirect plain HTTP → HTTPS (prod only)
"""

import logging
import time
from collections import defaultdict
from typing import Callable

from starlette.datastructures import Headers
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


# ── 1. Request logging ────────────────────────────────────────────────────────

class RequestLoggingMiddleware:
    """Logs method, path, status code and wall-clock response time."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request   = Request(scope)
        start     = time.perf_counter()
        status    = 0

        async def send_with_logging(message: dict) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        await self.app(scope, receive, send_with_logging)

        duration_ms = (time.perf_counter() - start) * 1000
        # Skip noisy static asset logs in development
        path = request.url.path
        if not path.startswith("/static"):
            logger.info(
                "%s %s → %d  (%.1fms)",
                request.method, path, status, duration_ms,
            )


# ── 2. Security headers ───────────────────────────────────────────────────────

class SecurityHeadersMiddleware:
    """
    Adds hardened HTTP security headers to every response.
    CSP is set to a strict baseline — tighten further as the app grows.
    """

    _HEADERS = {
        # Prevent MIME-type sniffing
        "X-Content-Type-Options": "nosniff",
        # Deny framing (clickjacking protection)
        "X-Frame-Options": "DENY",
        # Force HTTPS for 1 year (including subdomains) — browser-side
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        # Disable legacy XSS filter (CSP is the modern replacement)
        "X-XSS-Protection": "0",
        # Limit referrer information sent to third parties
        "Referrer-Policy": "strict-origin-when-cross-origin",
        # Restrict browser feature access
        "Permissions-Policy": (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), interest-cohort=()"
        ),
        # Content Security Policy
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob: https://*.supabase.co; "
            "connect-src 'self' https://*.supabase.co wss://*.supabase.co; "
            "frame-ancestors 'none';"
        ),
    }

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                for name, value in self._HEADERS.items():
                    headers.append((name.lower().encode(), value.encode()))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)


# ── 3. Rate limiter ───────────────────────────────────────────────────────────

class RateLimitMiddleware:
    """
    Sliding-window per-IP rate limiter.

    Two tiers:
      • Global  — 300 requests / 60 s   (protects all routes)
      • Auth    — 20  requests / 60 s   (stricter on /check-identifier,
                                          /register, /verify-otp, /set-pin,
                                          /resend-otp)
    Returns 429 with Retry-After header on breach.
    """

    _AUTH_PATHS = {
        "/check-identifier",
        "/register",
        "/verify-otp",
        "/set-pin",
        "/resend-otp",
    }

    def __init__(
        self,
        app: ASGIApp,
        *,
        global_limit: int = 300,
        global_window: int = 60,
        auth_limit: int = 20,
        auth_window: int = 60,
    ) -> None:
        self.app           = app
        self.global_limit  = global_limit
        self.global_window = global_window
        self.auth_limit    = auth_limit
        self.auth_window   = auth_window
        # {ip: [timestamp, ...]}
        self._global: dict[str, list[float]] = defaultdict(list)
        self._auth:   dict[str, list[float]] = defaultdict(list)

    def _get_ip(self, scope: Scope) -> str:
        # Respect reverse-proxy headers if present
        headers = Headers(scope=scope)
        return (
            headers.get("x-forwarded-for", "").split(",")[0].strip()
            or headers.get("x-real-ip", "")
            or (scope.get("client") or ("unknown", 0))[0]
        )

    def _is_limited(
        self, store: dict[str, list[float]], ip: str, limit: int, window: int
    ) -> tuple[bool, int]:
        now    = time.monotonic()
        times  = store[ip]
        times[:] = [t for t in times if now - t < window]
        if len(times) >= limit:
            retry_after = int(window - (now - times[0])) + 1
            return True, retry_after
        times.append(now)
        return False, 0

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        ip   = self._get_ip(scope)
        path = scope.get("path", "")

        # Global check
        limited, retry = self._is_limited(
            self._global, ip, self.global_limit, self.global_window
        )
        if limited:
            logger.warning("Rate limit (global) exceeded ip=%s path=%s", ip, path)
            resp = PlainTextResponse(
                "Too many requests. Please slow down.",
                status_code=429,
                headers={"Retry-After": str(retry)},
            )
            await resp(scope, receive, send)
            return

        # Auth-route check
        if path in self._AUTH_PATHS:
            limited, retry = self._is_limited(
                self._auth, ip, self.auth_limit, self.auth_window
            )
            if limited:
                logger.warning("Rate limit (auth) exceeded ip=%s path=%s", ip, path)
                resp = PlainTextResponse(
                    "Too many authentication attempts. Please wait and try again.",
                    status_code=429,
                    headers={"Retry-After": str(retry)},
                )
                await resp(scope, receive, send)
                return

        await self.app(scope, receive, send)


# ── Factory ───────────────────────────────────────────────────────────────────

def apply_middleware(app: ASGIApp, *, is_production: bool) -> ASGIApp:
    """
    Wrap the app with all middleware in the correct order.
    Call once after all routes are registered on the FastHTML app.

    Starlette middleware is applied bottom-up: last added = outermost
    (first to receive a request, last to send a response).

    NOTE: HTTPSRedirectMiddleware is intentionally omitted.
    All deployment platforms (Railway, Render, Fly.io) terminate TLS at
    the edge and forward plain HTTP to the container. Adding
    HTTPSRedirectMiddleware here causes infinite 307 redirect loops because
    the container only ever sees HTTP. Let the platform handle HTTPS.
    """
    # Always active
    app = GZipMiddleware(app, minimum_size=1024)
    app = RateLimitMiddleware(app)
    app = SecurityHeadersMiddleware(app)
    app = RequestLoggingMiddleware(app)

    return app
