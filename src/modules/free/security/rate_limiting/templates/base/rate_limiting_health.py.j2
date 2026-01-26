"""Shared health helpers for Rate Limiting runtime."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping, Sequence

from src.modules.free.security.rate_limiting.rate_limiting_types import RateLimiterHealthSnapshot, as_dict

_RATE_LIMITING_FEATURES: tuple[str, ...] = (
    "configurable_rules",
    "distributed_backend",
    "http_headers",
)


def build_health_snapshot(
    metadata: Mapping[str, Any] | None,
    *,
    module_name: str = "rate_limiting",
    status: str | None = None,
    detail: str | None = None,
    features: Sequence[str] | None = None,
) -> RateLimiterHealthSnapshot:
    """Construct a typed snapshot from the runtime metadata mapping."""

    feature_set = tuple(features) if features is not None else _RATE_LIMITING_FEATURES
    payload: MutableMapping[str, Any] = {
        "module": module_name,
        "checked_at": datetime.now(timezone.utc),
    }
    if metadata:
        payload.update(dict(metadata))
    if status:
        payload["status"] = status
    return RateLimiterHealthSnapshot.from_mapping(
        payload,
        module_name=module_name,
        features=feature_set,
        detail=detail,
    )


def render_health_snapshot(snapshot: RateLimiterHealthSnapshot) -> MutableMapping[str, Any]:
    """Serialize a typed health snapshot into a JSON-serializable payload."""

    return as_dict(snapshot)


def build_metadata(metadata: Mapping[str, Any] | None) -> MutableMapping[str, Any]:
    """Return a JSON-serializable metadata payload for the rate limiter."""

    snapshot = build_health_snapshot(metadata)
    return as_dict(snapshot)


RATE_LIMITING_FEATURES = _RATE_LIMITING_FEATURES

__all__ = [
    "RATE_LIMITING_FEATURES",
    "build_health_snapshot",
    "build_metadata",
    "render_health_snapshot",
]
