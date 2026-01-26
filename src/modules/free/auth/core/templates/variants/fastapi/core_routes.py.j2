"""FastAPI routes exposing Auth Core metadata and diagnostics."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, status

from src.modules.free.auth.core.auth.core import describe_auth_core, list_auth_core_features

router = APIRouter(prefix="/api/auth/core", tags=["auth-core"])


@router.get(
    "/metadata",
    status_code=status.HTTP_200_OK,
    summary="Retrieve Auth Core runtime metadata",
)
async def auth_core_metadata() -> Dict[str, Any]:
    """Return an enriched metadata payload for the Auth Core subsystem."""

    return describe_auth_core()


@router.get(
    "/features",
    status_code=status.HTTP_200_OK,
    summary="List Auth Core feature flags",
)
async def auth_core_features() -> Dict[str, Any]:
    """Expose the features advertised by the Auth Core module."""

    return {"features": list_auth_core_features()}


__all__ = ["router", "auth_core_metadata", "auth_core_features"]
