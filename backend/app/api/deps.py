"""
Shared API dependencies — authentication, rate limiting, service injection.
"""

import time
from collections import defaultdict
from typing import Optional

from fastapi import Request, Depends, Header
from app.config import get_settings, Settings
from app.utils.exceptions import RateLimitExceededError


# ── Simple in-memory rate limiter ────────────────────────────────────────────

_request_counts: dict[str, list[float]] = defaultdict(list)


async def rate_limiter(request: Request):
    """
    Simple per-IP rate limiter.
    In production, replace with Redis-backed solution.
    """
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60  # 1 minute

    # Clean old entries
    _request_counts[client_ip] = [
        t for t in _request_counts[client_ip] if now - t < window
    ]

    if len(_request_counts[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
        raise RateLimitExceededError()

    _request_counts[client_ip].append(now)


# ── Optional API key auth ────────────────────────────────────────────────────

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Optional API key verification.
    In production, enforce this for all endpoints.
    For development, allow requests without a key.
    """
    # Currently permissive — add key validation logic here
    pass


# ── Settings dependency ──────────────────────────────────────────────────────

async def get_config() -> Settings:
    """Inject settings into route handlers."""
    return get_settings()
