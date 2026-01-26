"""FastAPI router exposing CORS configuration metadata."""

from __future__ import annotations

from typing import Any, Dict, Mapping

from fastapi import APIRouter, FastAPI, Request

from src.health.cors import build_health_snapshot, render_health_snapshot

router = APIRouter(prefix="/security/cors", tags=["security", "cors"])


def _extract_cors_config(app: FastAPI) -> Mapping[str, Any]:
    state = getattr(app, "state", None)
    if state is None:
        return {}
    config = getattr(state, "cors_settings", None)
    if isinstance(config, Mapping):
        return config
    config_obj = getattr(state, "cors_config", None)
    if config_obj is None:
        return {}
    if hasattr(config_obj, "model_dump"):
        return config_obj.model_dump()
    if hasattr(config_obj, "dict"):
        return config_obj.dict()
    return {}


@router.get("/metadata", response_model=Dict[str, Any])
async def get_cors_metadata(request: Request) -> Dict[str, Any]:
    """Return metadata describing the current CORS middleware configuration."""

    config = _extract_cors_config(request.app)
    snapshot = build_health_snapshot(config)
    return render_health_snapshot(snapshot)


@router.get("/features", response_model=Dict[str, Any])
async def list_cors_features(request: Request) -> Dict[str, Any]:
    """List feature flags supported by the CORS module."""

    config = _extract_cors_config(request.app)
    snapshot = build_health_snapshot(config)
    return {"features": list(snapshot.features)}


def register_cors_routes(app: FastAPI) -> None:
    """Attach the CORS routes to a FastAPI application."""

    app.include_router(router)


__all__ = [
    "get_cors_metadata",
    "list_cors_features",
    "register_cors_routes",
    "router",
]
