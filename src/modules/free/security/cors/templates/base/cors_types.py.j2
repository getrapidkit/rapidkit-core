"""Typed helpers for CORS module metadata serialization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping, Sequence


@dataclass(frozen=True)
class CorsPolicySnapshot:
    """Canonical view of an application's configured CORS policy."""

    allow_origins: tuple[str, ...]
    allow_credentials: bool
    allow_methods: tuple[str, ...]
    allow_headers: tuple[str, ...]
    expose_headers: tuple[str, ...]
    max_age: int

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> "CorsPolicySnapshot":
        data = payload or {}
        allow_origins = _normalize_sequence(data.get("allow_origins"), default=("*",))
        allow_methods = _normalize_sequence(data.get("allow_methods"), default=("*",))
        allow_headers = _normalize_sequence(data.get("allow_headers"), default=("*",))
        expose_headers = _normalize_sequence(data.get("expose_headers"), default=())
        allow_credentials = bool(data.get("allow_credentials", True))
        max_age_raw = data.get("max_age", 600)
        try:
            max_age = int(max_age_raw)
        except (TypeError, ValueError):
            max_age = 600
        return cls(
            allow_origins=allow_origins,
            allow_credentials=allow_credentials,
            allow_methods=allow_methods,
            allow_headers=allow_headers,
            expose_headers=expose_headers,
            max_age=max_age,
        )

    def as_dict(self) -> MutableMapping[str, Any]:
        """Return the snapshot as a JSON-serializable mapping."""

        return {
            "allow_origins": list(self.allow_origins),
            "allow_credentials": self.allow_credentials,
            "allow_methods": list(self.allow_methods),
            "allow_headers": list(self.allow_headers),
            "expose_headers": list(self.expose_headers),
            "max_age": self.max_age,
        }


def _normalize_sequence(value: Any, *, default: Sequence[str]) -> tuple[str, ...]:
    if value is None:
        return tuple(default)
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(str(item) for item in value if isinstance(item, str) and item)
    return tuple(default)


@dataclass(frozen=True)
class CorsHealthSnapshot:
    """Typed representation of the CORS health payload."""

    module: str
    status: str
    checked_at: datetime
    enabled: bool
    policy: CorsPolicySnapshot
    features: tuple[str, ...]
    detail: str | None = None
    log_level: str | None = None
    metadata: Mapping[str, Any] | None = None

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
        *,
        default_module: str = "cors",
    ) -> "CorsHealthSnapshot":
        module = str(payload.get("module", default_module))
        status = str(payload.get("status", "unknown"))
        checked_at_raw = payload.get("checked_at")
        if isinstance(checked_at_raw, datetime):
            checked_at = checked_at_raw
        elif checked_at_raw:
            try:
                checked_at = datetime.fromisoformat(str(checked_at_raw)).replace(tzinfo=timezone.utc)
            except ValueError:
                checked_at = datetime.now(timezone.utc)
        else:
            checked_at = datetime.now(timezone.utc)
        if checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=timezone.utc)

        enabled = bool(payload.get("enabled", True))
        policy_payload = payload.get("policy")
        policy = (
            policy_payload
            if isinstance(policy_payload, CorsPolicySnapshot)
            else CorsPolicySnapshot.from_mapping(policy_payload if isinstance(policy_payload, Mapping) else None)
        )
        features_raw = payload.get("features", ())
        features = tuple(
            str(feature)
            for feature in features_raw
            if isinstance(feature, str) and feature
        )
        metadata_raw = payload.get("metadata")
        metadata = (
            metadata_raw
            if isinstance(metadata_raw, Mapping)
            else {}
        )
        log_level = payload.get("log_level")
        log_level_str = str(log_level) if log_level is not None else None
        return cls(
            module=module,
            status=status,
            checked_at=checked_at,
            enabled=enabled,
            policy=policy,
            features=features,
            detail=str(payload.get("detail")) if payload.get("detail") else None,
            log_level=log_level_str,
            metadata=metadata,
        )


def as_dict(snapshot: CorsHealthSnapshot) -> MutableMapping[str, Any]:
    """Convert a typed snapshot to a JSON-serializable payload."""

    payload: MutableMapping[str, Any] = {
        "module": snapshot.module,
        "status": snapshot.status,
        "checked_at": snapshot.checked_at.isoformat(),
        "enabled": snapshot.enabled,
        "policy": snapshot.policy.as_dict(),
        "features": list(snapshot.features),
    }
    if snapshot.detail:
        payload["detail"] = snapshot.detail
    if snapshot.log_level:
        payload["log_level"] = snapshot.log_level
    if snapshot.metadata:
        payload["metadata"] = dict(snapshot.metadata)
    return payload


__all__ = [
    "CorsPolicySnapshot",
    "CorsHealthSnapshot",
    "as_dict",
]
