"""FastAPI dependency helpers for the Rate Limiting module."""

from __future__ import annotations

from functools import lru_cache
from typing import Awaitable, Callable

from fastapi import Depends, HTTPException, Request, Response

from src.modules.free.security.rate_limiting import (
    RateLimitResult,
    RateLimiter,
    RateLimiterConfig,
    configure_rate_limiter,
    load_rate_limiter_config,
)


@lru_cache(maxsize=1)
def get_rate_limiter_config() -> RateLimiterConfig:
    """Load and cache the resolved rate limiter configuration."""

    return load_rate_limiter_config()


@lru_cache(maxsize=1)
def get_rate_limiter_instance() -> RateLimiter:
    """Initialise the shared rate limiter for dependency injection."""

    return configure_rate_limiter(get_rate_limiter_config())


def _resolve_identity(request: Request, config: RateLimiterConfig) -> str | None:
    header_name = config.identity_header
    if header_name:
        header_identity = request.headers.get(header_name)
        if header_identity:
            return header_identity

    if config.trust_forwarded_for:
        forwarded = request.headers.get(config.forwarded_for_header)
        if forwarded:
            return forwarded.split(",", 1)[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return None


RateLimitDependency = Callable[[Request, Response, RateLimiter], Awaitable[RateLimitResult]]


def rate_limit_dependency(*, rule: str | None = None, cost: int | None = None) -> RateLimitDependency:
    """Factory returning a FastAPI dependency that enforces rate limits."""

    async def _dependency(
        request: Request,
        response: Response,
        limiter: RateLimiter = Depends(get_rate_limiter_instance),
    ) -> RateLimitResult:
        identity = _resolve_identity(request, limiter.config)
        result = await limiter.consume(
            identity=identity,
            method=request.method,
            path=request.url.path,
            cost=cost,
            rule_name=rule,
            raise_on_failure=False,
        )

        headers = result.to_headers(limiter.config.headers)
        for key, value in headers.items():
            response.headers[key] = value

        if not result.allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for rule '{result.rule.name}'",
                headers=headers,
            )

        return result

    return _dependency


__all__ = [
    "get_rate_limiter_config",
    "get_rate_limiter_instance",
    "RateLimitDependency",
    "rate_limit_dependency",
]
