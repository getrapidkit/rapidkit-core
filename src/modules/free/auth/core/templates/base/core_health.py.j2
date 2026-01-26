"""Shared Auth Core health router with FastAPI fallbacks."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any, Dict, Mapping, cast

from src.modules.free.auth.core.auth.core import get_auth_core_metadata
from src.modules.free.auth.core.auth.core_types import AuthCoreHealthSnapshot, as_dict

APIRouter: Any
FastAPIApp: Any
status: Any
JSONResponse: Any

try:  # pragma: no cover - FastAPI optional at import time
    from fastapi import APIRouter, Depends, FastAPI as FastAPIApp, status
    from fastapi.responses import JSONResponse
except ImportError:  # pragma: no cover - allow import without FastAPI installed
    APIRouter = cast(Any, None)
    FastAPIApp = cast(Any, None)
    JSONResponse = None
    status = SimpleNamespace(HTTP_200_OK=200, HTTP_503_SERVICE_UNAVAILABLE=503)
    _FASTAPI_AVAILABLE = False
else:
    _FASTAPI_AVAILABLE = True

logger = logging.getLogger("auth_core.health")

if _FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/api/health/module", tags=["health"])
else:  # pragma: no cover - executed only without FastAPI
    router = None


def _collect_snapshot() -> AuthCoreHealthSnapshot:
    metadata: Mapping[str, Any] = get_auth_core_metadata()
    return AuthCoreHealthSnapshot.from_mapping(metadata)


if _FASTAPI_AVAILABLE:

    @router.get(  # type: ignore[union-attr]
        "/auth-core",
        summary="Auth Core module health check",
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_503_SERVICE_UNAVAILABLE: {
                "description": "Auth Core runtime unavailable",
            }
        },
    )
    async def auth_core_health_check(  # pragma: no cover - exercised at integration level
        snapshot: AuthCoreHealthSnapshot = Depends(_collect_snapshot),
    ) -> Dict[str, Any]:
        """Return the Auth Core health payload."""

        payload: Dict[str, Any] = as_dict(snapshot)
        payload.update({"status": "ok"})
        return payload

else:  # pragma: no cover - executed only without FastAPI

    async def auth_core_health_check() -> Dict[str, Any]:  # type: ignore[override]
        raise RuntimeError("FastAPI must be installed to expose Auth Core health endpoints")


def register_auth_core_health(app: Any) -> None:
    """Attach the Auth Core health router to a FastAPI app."""

    if not _FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI must be installed to register Auth Core health routes")
    if FastAPIApp is not None and not isinstance(app, FastAPIApp):  # pragma: no cover
        raise TypeError("register_auth_core_health expects a FastAPI application instance")
    if router is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Auth Core health router unavailable")

    app.include_router(router)


__all__ = ["AuthCoreHealthSnapshot", "auth_core_health_check", "register_auth_core_health", "router"]
