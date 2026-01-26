"""FastAPI router exposing Rate Limiting metadata and feature discovery."""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, FastAPI

from src.health.rate_limiting import (
    RATE_LIMITING_FEATURES,
    build_health_snapshot,
    render_health_snapshot,
)
from src.modules.free.security.rate_limiting import get_rate_limiter_metadata

router = APIRouter(prefix="/security/rate-limiting", tags=["security", "rate-limiting"])


@router.get("/metadata", response_model=Dict[str, object])
async def get_rate_limiting_metadata() -> Dict[str, object]:
    """Expose the configured rate limiting metadata."""

    metadata = get_rate_limiter_metadata()
    snapshot = build_health_snapshot(metadata, features=RATE_LIMITING_FEATURES)
    return render_health_snapshot(snapshot)


@router.get("/features", response_model=Dict[str, object])
async def list_rate_limiting_features() -> Dict[str, object]:
    """List capabilities advertised by the Rate Limiting module."""

    return {"features": list(RATE_LIMITING_FEATURES)}


def register_rate_limiting_routes(app: FastAPI) -> None:
    """Attach the Rate Limiting metadata routes to a FastAPI application."""

    app.include_router(router)


__all__ = [
    "get_rate_limiting_metadata",
    "list_rate_limiting_features",
    "register_rate_limiting_routes",
    "router",
]
