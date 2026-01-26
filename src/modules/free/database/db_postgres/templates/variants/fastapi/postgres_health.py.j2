"""FastAPI router exposing PostgreSQL health information."""

from __future__ import annotations

import platform
from types import SimpleNamespace
from typing import Any, Dict, cast

from src.modules.free.database.db_postgres.postgres import (  # type: ignore[import]
    check_postgres_connection,
    get_database_url,
    get_pool_status,
)
import logging

APIRouter: Any
status: Any
JSONResponse: Any

try:
    from fastapi import APIRouter, status
    from fastapi.responses import JSONResponse
except ImportError:  # pragma: no cover - allow import without FastAPI installed
    APIRouter = cast(Any, None)
    status = SimpleNamespace(HTTP_200_OK=200)  # type: ignore[assignment]
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
        except Exception as exc:  # pragma: no cover - defensive guard
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

    async def postgres_health_check() -> Dict[str, Any]:  # type: ignore[override]
        """Stub raising an error when FastAPI is missing."""

        raise RuntimeError("FastAPI must be installed to expose PostgreSQL health endpoints")


def register_postgres_health(app: Any) -> None:
    """Attach the PostgreSQL health router to the provided FastAPI application."""

    if not _FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI must be installed to register PostgreSQL health routes")
    if router is None:  # pragma: no cover - defensive guard
        raise RuntimeError("PostgreSQL health router unavailable")

    app.include_router(router)


__all__ = [
    "postgres_health_check",
    "register_postgres_health",
]
