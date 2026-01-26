"""Minimal middleware health router for runtime tests."""

from __future__ import annotations

import logging
import sys as _sys
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict, cast

APIRouter: Any
FastAPI: Any
status: Any
JSONResponse: Any

try:
    from fastapi import APIRouter, FastAPI, status
    from fastapi.responses import JSONResponse
except ImportError:  # pragma: no cover - optional dependency for tests
    APIRouter = cast(Any, None)
    FastAPI = cast(Any, None)
    status = SimpleNamespace(HTTP_200_OK=200, HTTP_503_SERVICE_UNAVAILABLE=503)
    JSONResponse = None
    _FASTAPI_AVAILABLE = False
else:
    _FASTAPI_AVAILABLE = True

logger = logging.getLogger("middleware.health")

_MIDDLEWARE_COUNT = 3
_MODULE_NAME = "middleware"
_MODULE_VERSION = "runtime"


def _build_payload() -> Dict[str, Any]:
    return {
        "status": "ok",
        "module": _MODULE_NAME,
        "module_version": _MODULE_VERSION,
        "middleware_count": _MIDDLEWARE_COUNT,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


if _FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/api/health/module", tags=["health"])

    @router.get(
        "/middleware",
        summary="Middleware module health check",
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_503_SERVICE_UNAVAILABLE: {
                "description": "Middleware subsystem unavailable",
            }
        },
    )
    async def middleware_health_check() -> Any:
        try:
            payload = _build_payload()
        except Exception as exc:  # pragma: no cover - defensive guard
            message = str(exc) or "middleware health check failed"
            logger.exception("Middleware health check failed")
            if JSONResponse is None:  # pragma: no cover - defensive guard
                return {
                    "status": "error",
                    "module": _MODULE_NAME,
                    "detail": message,
                }
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "error",
                    "module": _MODULE_NAME,
                    "detail": message,
                },
            )

        logger.debug("Middleware health endpoint invoked", extra={"payload": payload})
        return payload

else:  # pragma: no cover - executed only when FastAPI is unavailable
    router = cast(Any, None)

    async def middleware_health_check() -> Dict[str, Any]:
        raise RuntimeError("FastAPI must be installed to expose middleware health endpoints")


def register_middleware_health(app: Any) -> None:
    """Attach the middleware health router to the provided FastAPI application."""

    if not _FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI must be installed to register middleware health routes")
    if router is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Middleware health router unavailable")

    app.include_router(router)


__all__ = [
    "middleware_health_check",
    "register_middleware_health",
    "router",
]

_module = _sys.modules[__name__]
_sys.modules.setdefault("src.health.middleware", _module)
_sys.modules.setdefault("core.health.middleware", _module)

del _module
