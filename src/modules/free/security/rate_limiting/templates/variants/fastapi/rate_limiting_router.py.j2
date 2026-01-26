"""FastAPI router exposing operational Rate Limiting endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.modules.free.security.rate_limiting import RateLimitResult, RateLimiter
from src.modules.free.security.rate_limiting.dependencies import (
    get_rate_limiter_instance,
    rate_limit_dependency,
)

router = APIRouter(prefix="/api/rate-limits", tags=["rate-limiting"])


@router.get("/metadata", response_model=Dict[str, Any])
async def get_rate_limit_metadata(
    limiter: RateLimiter = Depends(get_rate_limiter_instance),
) -> Dict[str, Any]:
    """Return the configured rate limiter metadata for observability."""

    return limiter.get_metadata()


@router.get("/probe")
async def probe_rate_limit(
    result: RateLimitResult = Depends(rate_limit_dependency()),
) -> Dict[str, Any]:
    """Lightweight probe illustrating rate limiting behaviour."""

    return {
        "allowed": result.allowed,
        "remaining": result.remaining,
        "resetAfter": result.reset_after,
        "resetAt": result.reset_at,
        "limit": result.limit,
        "rule": result.rule.name,
        "bucket": result.bucket,
    }


__all__ = [
    "router",
    "get_rate_limit_metadata",
    "probe_rate_limit",
]
