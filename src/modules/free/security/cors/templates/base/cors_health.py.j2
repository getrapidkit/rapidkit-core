"""Framework-agnostic helpers for exposing CORS health metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping

from src.modules.free.security.cors.cors_types import CorsHealthSnapshot, CorsPolicySnapshot, as_dict

_CORS_FEATURES: tuple[str, ...] = (
    "cors_middleware",
    "http_security_headers",
)


def build_policy_snapshot(config: Mapping[str, Any] | None) -> CorsPolicySnapshot:
    """Create a typed policy snapshot from an application configuration mapping."""

    return CorsPolicySnapshot.from_mapping(config)


def build_health_snapshot(
    config: Mapping[str, Any] | None,
    *,
    module_name: str = "cors",
    status: str | None = None,
    detail: str | None = None,
) -> CorsHealthSnapshot:
    """Construct a typed health snapshot for downstream adapters."""

    cfg = dict(config or {})
    enabled = bool(cfg.get("enabled", True))
    resolved_status = status or ("ok" if enabled else "disabled")
    policy = build_policy_snapshot(cfg)
    log_level = str(cfg.get("log_level", "INFO"))
    metadata = cfg.get("metadata")
    if not isinstance(metadata, Mapping):
        metadata = {}

    return CorsHealthSnapshot(
        module=module_name,
        status=resolved_status,
        checked_at=datetime.now(timezone.utc),
        enabled=enabled,
        policy=policy,
        features=_CORS_FEATURES,
        detail=detail,
        log_level=log_level,
        metadata=dict(metadata),
    )


def render_health_snapshot(snapshot: CorsHealthSnapshot) -> MutableMapping[str, Any]:
    """Serialize a typed snapshot into a JSON payload."""

    return as_dict(snapshot)


def build_metadata(config: Mapping[str, Any] | None) -> MutableMapping[str, Any]:
    """Return a JSON-serializable metadata payload for CORS."""

    snapshot = build_health_snapshot(config)
    payload = as_dict(snapshot)
    payload.setdefault("module", snapshot.module)
    return payload


__all__ = [
    "build_health_snapshot",
    "build_metadata",
    "build_policy_snapshot",
    "render_health_snapshot",
]
