"""Shared Email health router with optional FastAPI integration."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any, Dict, Mapping, cast

from src.modules.free.communication.email.email import describe_email
from src.modules.free.communication.email.email_types import EmailHealthSnapshot, as_dict

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

logger = logging.getLogger("communication.email.health")

if _FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/api/health/module", tags=["health"])
else:  # pragma: no cover - executed only when FastAPI unavailable
    router = None


def _collect_snapshot() -> EmailHealthSnapshot:
    metadata: Mapping[str, Any] = describe_email()
    return EmailHealthSnapshot.from_mapping(metadata)


if _FASTAPI_AVAILABLE:

    @router.get(  # type: ignore[union-attr]
        "/email",
        summary="Email module health check",
        status_code=status.HTTP_200_OK,
    )
    async def email_health_check(  # pragma: no cover - exercised in integration tests
        snapshot: EmailHealthSnapshot = Depends(_collect_snapshot),
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = as_dict(snapshot)
        payload.update({"status": "ok"})
        logger.debug("Email health payload generated", extra={"payload": payload})
        return payload

else:  # pragma: no cover - executed only without FastAPI

    async def email_health_check() -> Dict[str, Any]:  # type: ignore[override]
        raise RuntimeError("FastAPI must be installed to expose Email health endpoints")


def register_email_health(app: Any) -> None:
    """Attach the shared Email health router to a FastAPI app."""

    if not _FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI must be installed to register Email health routes")
    if FastAPIApp is not None and not isinstance(app, FastAPIApp):  # pragma: no cover
        raise TypeError("register_email_health expects a FastAPI application instance")
    if router is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Email health router unavailable")

    app.include_router(router)


__all__ = ["email_health_check", "register_email_health", "router"]
