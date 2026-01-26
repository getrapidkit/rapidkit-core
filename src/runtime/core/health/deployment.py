"""Minimal deployment health router for runtime tests."""

from __future__ import annotations

import logging
import platform
import sys as _sys
from types import SimpleNamespace
from typing import Any, Dict, cast

APIRouter: Any
status: Any
JSONResponse: Any

try:
    from fastapi import APIRouter, status
    from fastapi.responses import JSONResponse
except ImportError:  # pragma: no cover - optional for unit tests
    APIRouter = cast(Any, None)
    status = SimpleNamespace(HTTP_200_OK=200)
    JSONResponse = None
    _FASTAPI_AVAILABLE = False
else:
    _FASTAPI_AVAILABLE = True

logger = logging.getLogger("deployment.health")

_DEFAULT_PAYLOAD: Dict[str, Any] = {
    "status": "ok",
    "module": "deployment",
    "runtime": "python",
    "ci": {"workflows": []},
    "services": {},
}


def _build_health_payload(hostname: str) -> Dict[str, Any]:
    payload = dict(_DEFAULT_PAYLOAD)
    payload["hostname"] = hostname
    return payload


if _FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/api/health/module", tags=["health"])

    @router.get(
        "/deployment",
        status_code=status.HTTP_200_OK,
        summary="Deployment module health check",
        responses={
            status.HTTP_503_SERVICE_UNAVAILABLE: {
                "description": "Deployment subsystem unavailable",
            }
        },
    )
    async def deployment_health_check() -> Any:
        try:
            hostname = platform.node()
        except Exception as exc:  # pragma: no cover - defensive guard
            message = str(exc) or "deployment health check failed"
            logger.exception("Deployment health check failed")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "error",
                    "module": "deployment",
                    "detail": message,
                },
            )

        payload = _build_health_payload(hostname)
        logger.debug("Deployment health endpoint invoked", extra={"payload": payload})
        return payload

else:  # pragma: no cover - executed only when FastAPI is unavailable
    router = cast(Any, None)

    async def deployment_health_check() -> Dict[str, Any]:
        raise RuntimeError("FastAPI must be installed to expose deployment health endpoints")


def register_deployment_health(app: Any) -> None:
    """Attach the deployment health router to the provided FastAPI application."""

    if not _FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI must be installed to register deployment health routes")
    if router is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Deployment health router unavailable")

    app.include_router(router)


__all__ = ["deployment_health_check", "register_deployment_health"]

_module = _sys.modules[__name__]
_sys.modules.setdefault("src.health.deployment", _module)
_sys.modules.setdefault("core.health.deployment", _module)

del _module
