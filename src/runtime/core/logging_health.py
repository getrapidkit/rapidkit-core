"""Canonical FastAPI health router and helpers for the logging module."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, cast

from .logging import get_logger, get_logging_metadata

APIRouter: Any
FastAPIApp: Any
status: Any
JSONResponse: Any

try:  # Import FastAPI when available but remain import-safe otherwise
    from fastapi import APIRouter, FastAPI as FastAPIApp, status
    from fastapi.responses import JSONResponse
except ImportError:  # pragma: no cover - module must stay importable without FastAPI
    APIRouter = cast(Any, None)
    FastAPIApp = cast(Any, None)
    status = SimpleNamespace(HTTP_200_OK=200)
    JSONResponse = None
    _FASTAPI_AVAILABLE = False
else:
    _FASTAPI_AVAILABLE = True

logger = get_logger("logging.health")

router: Any = (
    APIRouter(prefix="/api/health/module", tags=["health"])
    if _FASTAPI_AVAILABLE
    else cast(Any, None)
)


def collect_logging_health() -> Dict[str, Any]:
    """Return aggregated metadata about the logging runtime."""

    payload: Dict[str, Any] = {
        "module": "logging",
        "module_version": "1.0.0",
        "status": "ok",
    }

    try:
        vendor_metadata = get_logging_metadata()
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.exception("Failed to collect logging metadata")
        payload.update({"status": "error", "detail": str(exc) or "unknown failure"})
        return payload

    payload.update(vendor_metadata)
    return payload


def build_health_payload(status: str = "ok", **extras: Any) -> Dict[str, Any]:
    """Construct a canonical health payload for downstream frameworks."""

    payload: Dict[str, Any] = {
        "module": "logging",
        "module_version": "1.0.0",
        "status": status,
    }
    if extras:
        payload.update(extras)
    return payload


if _FASTAPI_AVAILABLE:

    @router.get(
        "/logging",
        status_code=status.HTTP_200_OK,
        summary="Logging module health check",
        responses={
            status.HTTP_503_SERVICE_UNAVAILABLE: {
                "description": "Logging subsystem unavailable",
            }
        },
    )
    async def logging_health_check() -> Any:
        """Return status information about the logging subsystem."""

        payload = collect_logging_health()
        if payload.get("status") != "ok":
            if JSONResponse is None:  # pragma: no cover - defensive guard
                return payload
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=payload,
            )

        logger.debug("Logging health endpoint invoked", extra={"payload": payload})
        return payload

else:  # pragma: no cover - executed only when FastAPI is unavailable

    async def logging_health_check() -> Dict[str, Any]:
        """Stub that surfaces a consistent error when FastAPI is unavailable."""

        raise RuntimeError("FastAPI must be installed to use logging health endpoints")


def register_logging_health(app: Any) -> None:
    """Attach the logging health router to the provided FastAPI application."""

    if not _FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI must be installed to register logging health routes")
    if FastAPIApp is not None and not isinstance(
        app, FastAPIApp
    ):  # pragma: no cover - runtime guard
        raise TypeError("register_logging_health expects a FastAPI application instance")
    if router is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Logging health router unavailable")

    app.include_router(router)


__all__ = [
    "collect_logging_health",
    "build_health_payload",
    "logging_health_check",
    "register_logging_health",
    "router",
    "logger",
]
