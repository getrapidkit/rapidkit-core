"""FastAPI router exposing Redis module health information."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from types import SimpleNamespace
from typing import Any, Dict, cast

try:
    from src.modules.free.cache.redis.client import check_redis_connection, get_redis_metadata
    from src.modules.free.cache.redis.redis_types import RedisHealthSnapshot, as_dict
except ModuleNotFoundError:
    async def check_redis_connection() -> None:  # type: ignore
        raise ModuleNotFoundError("redis client not available")

    def get_redis_metadata() -> dict:  # type: ignore
        return {}

    class RedisHealthSnapshot:  # type: ignore
        def __init__(
            self,
            status: str = "unknown",
            checked_at: str | None = None,
            cache_ttl: int | None = None,
        ):
            self.status = status
            self.module = "redis"
            self.checked_at = checked_at or datetime.now(timezone.utc).isoformat()
            self.cache_ttl = cache_ttl

        @classmethod
        def collect(cls, metadata: dict) -> "RedisHealthSnapshot":
            return cls(status="ok", cache_ttl=metadata.get("cache_ttl"))

    def as_dict(snapshot: "RedisHealthSnapshot") -> dict:  # type: ignore
        return {
            "module": getattr(snapshot, "module", "redis"),
            "status": getattr(snapshot, "status", "unknown"),
            "checked_at": getattr(snapshot, "checked_at", None),
            "cache_ttl": getattr(snapshot, "cache_ttl", None),
        }

APIRouter: Any
FastAPIApp: Any
status: Any
JSONResponse: Any

try:
    from fastapi import APIRouter, Depends, FastAPI as FastAPIApp, status
    from fastapi.responses import JSONResponse
except ImportError:  # pragma: no cover - allow import without FastAPI installed
    APIRouter = cast(Any, None)
    FastAPIApp = cast(Any, None)
    JSONResponse = None
    status = SimpleNamespace(HTTP_200_OK=200)
    _FASTAPI_AVAILABLE = False
else:
    _FASTAPI_AVAILABLE = True

logger = logging.getLogger("redis.health")

if _FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/api/health/module", tags=["health"])
else:  # pragma: no cover - executed only without FastAPI
    router = None


def _collect_snapshot() -> RedisHealthSnapshot:
    return RedisHealthSnapshot.collect(get_redis_metadata())


if _FASTAPI_AVAILABLE:

    @router.get(  # type: ignore[union-attr]
        "/redis",
        summary="Redis module health check",
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_503_SERVICE_UNAVAILABLE: {
                "description": "Redis subsystem unavailable",
            }
        },
    )
    async def redis_health_check(snapshot: RedisHealthSnapshot = Depends(_collect_snapshot)) -> Any:
        """Return health information for the Redis integration."""

        try:
            await check_redis_connection()
        except Exception as exc:  # pragma: no cover - defensive guard
            message = str(exc) or "redis health check failed"
            logger.exception("Redis health check failed")
            if JSONResponse is None:  # pragma: no cover - fallback without FastAPI response
                return {
                    "status": "error",
                    "module": snapshot.module,
                    "detail": message,
                }
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "error",
                    "module": snapshot.module,
                    "detail": message,
                },
            )

        payload: Dict[str, Any] = as_dict(snapshot)
        payload.setdefault("checked_at", getattr(snapshot, "checked_at", None))
        payload.update({
            "status": "ok",
            "checks": {
                "connection": True,
                "cache_ttl": snapshot.cache_ttl is not None,
            },
        })
        logger.debug("Redis health endpoint invoked", extra={"payload": payload})
        return payload


else:  # pragma: no cover - executed only without FastAPI

    async def redis_health_check() -> Dict[str, Any]:  # type: ignore[override]
        """Stub raising an error when FastAPI support is unavailable."""

        raise RuntimeError("FastAPI must be installed to expose Redis health endpoints")


def register_redis_health(app: Any) -> None:
    """Attach the Redis health router to the provided FastAPI application."""

    if not _FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI must be installed to register Redis health routes")
    if FastAPIApp is not None and not isinstance(app, FastAPIApp):  # pragma: no cover
        raise TypeError("register_redis_health expects a FastAPI application instance")
    if router is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Redis health router unavailable")

    app.include_router(router)


__all__ = ["redis_health_check", "register_redis_health", "router"]
