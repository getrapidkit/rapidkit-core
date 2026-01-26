"""FastAPI router exposing PostgreSQL health information for runtime tests."""

from __future__ import annotations

import logging
import platform
import sys as _sys
from types import SimpleNamespace
from typing import Any, Dict, cast

from runtime.core.database.postgres import (
    check_postgres_connection,
    get_database_url,
    get_pool_status,
)

APIRouter: Any
status: Any
JSONResponse: Any

try:
    from fastapi import APIRouter, status
    from fastapi.responses import JSONResponse
except ImportError:  # pragma: no cover - optional dependency for tests
    APIRouter = cast(Any, None)
    status = SimpleNamespace(HTTP_200_OK=200)
    JSONResponse = None
    _FASTAPI_AVAILABLE = False
else:
    _FASTAPI_AVAILABLE = True

logger = logging.getLogger("database.postgres.health")

if _FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/api/health/module", tags=["health"])

    @router.get(
        "/postgres",
        status_code=status.HTTP_200_OK,
        summary="PostgreSQL module health check",
        responses={
            status.HTTP_503_SERVICE_UNAVAILABLE: {
                "description": "PostgreSQL subsystem unavailable",
            }
        },
    )
    async def postgres_health_check() -> Any:
        """Run async connection checks and emit pool metadata."""

        try:
            await check_postgres_connection()
            pool_status = await get_pool_status()
            hostname = platform.node()
        except Exception as exc:  # pragma: no cover - defensive guard for runtime tests
            message = str(exc) or "postgres health check failed"
            logger.exception("PostgreSQL health check failed")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "error",
                    "module": "db_postgres",
                    "detail": message,
                },
            )

        logger.debug("PostgreSQL health probe succeeded", extra={"pool": pool_status})

        return {
            "status": "ok",
            "module": "db_postgres",
            "url": get_database_url(hide_password=True),
            "hostname": hostname,
            "pool": pool_status,
        }

else:  # pragma: no cover - executed only when FastAPI is unavailable
    router = cast(Any, None)

    async def postgres_health_check() -> Dict[str, Any]:
        raise RuntimeError("FastAPI must be installed to expose PostgreSQL health endpoints")


def register_postgres_health(app: Any) -> None:
    """Attach the PostgreSQL health router to the provided FastAPI application."""

    if not _FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI must be installed to register PostgreSQL health routes")
    if router is None:  # pragma: no cover - defensive guard
        raise RuntimeError("PostgreSQL health router unavailable")

    app.include_router(router)


__all__ = ["postgres_health_check", "register_postgres_health"]

_module = _sys.modules[__name__]
_sys.modules.setdefault("src.health.database.postgres", _module)
_sys.modules.setdefault("core.health.database.postgres", _module)

del _module
