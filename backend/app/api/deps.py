"""
Shared API dependencies — authentication, rate limiting, service injection.
"""

import time
from collections import defaultdict
from typing import Optional

from fastapi import Request, Depends, Header
from app.config import get_settings, Settings
from app.utils.exceptions import RateLimitExceededError, InvalidAPIKeyError
from app.utils.logger import get_logger

logger = get_logger(__name__)


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


# ── API key extraction ───────────────────────────────────────────────────────

async def api_key_header(x_api_key: Optional[str] = Header(None)):
    """Extracts the X-API-Key header."""
    return x_api_key


# ── Mandatory API key auth ───────────────────────────────────────────────────

async def verify_api_key(
    settings: Settings = Depends(get_settings),
    api_key_header: Optional[str] = Depends(api_key_header),
) -> Optional[str]:
    """
    Verify the API key provided in the header.
    Mandatory for all routes using this dependency.
    """
    if not settings.API_KEY:
        # If no server-side key is configured, allow (dev mode)
        return None

    if not api_key_header:
        logger.warning("Missing API key in request")
        raise InvalidAPIKeyError(detail="API key is required")

    if api_key_header != settings.API_KEY:
        logger.warning(f"Invalid API key attempt: {api_key_header[:4]}...")
        raise InvalidAPIKeyError()

    return api_key_header


# ── Settings dependency ──────────────────────────────────────────────────────

async def get_config() -> Settings:
    """Inject settings into route handlers."""
    return get_settings()
