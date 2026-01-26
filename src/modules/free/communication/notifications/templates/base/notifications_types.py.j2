"""Typed helpers for Notifications module metadata serialization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timezone
from typing import Any, Mapping, MutableMapping, Sequence


@dataclass(frozen=True)
class NotificationProviderSnapshot:
    """Normalized snapshot describing a single notification provider."""

    name: str
    enabled: bool
    handler_registered: bool
    metadata: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, name: str, payload: Mapping[str, Any] | None) -> "NotificationProviderSnapshot":
        data = payload or {}
        return cls(
            name=name,
            enabled=bool(data.get("enabled", False)),
            handler_registered=bool(data.get("handler_registered", False)),
            metadata=dict(data.get("metadata", {})) if isinstance(data.get("metadata"), Mapping) else {},
        )


@dataclass(frozen=True)
class NotificationsHealthSnapshot:
    """Complete metadata snapshot consumed by health endpoints."""

    module: str
    version: str | None
    status: str
    checked_at: datetime
    providers: tuple[NotificationProviderSnapshot, ...]
    features: tuple[str, ...]
    detail: str | None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "NotificationsHealthSnapshot":
        module_name = str(payload.get("module", "notifications"))
        version = payload.get("version")
        status = str(payload.get("status", "unknown"))
        checked_at_raw = payload.get("checked_at")
        if isinstance(checked_at_raw, datetime):
            checked_at = checked_at_raw
        elif checked_at_raw:
            checked_at = datetime.fromisoformat(str(checked_at_raw))
        else:
            checked_at = datetime.now(timezone.utc)

        if checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=UTC)

        providers_payload = payload.get("providers")
        providers: Sequence[NotificationProviderSnapshot]
        if isinstance(providers_payload, Mapping):
            providers = tuple(
                NotificationProviderSnapshot.from_mapping(name, info)
                for name, info in sorted(providers_payload.items(), key=lambda item: item[0])
            )
        else:
            providers = ()

        features_payload = payload.get("features", ())
        features = tuple(str(feature) for feature in features_payload if isinstance(feature, str) and feature)
        return cls(
            module=module_name,
            version=str(version) if version is not None else None,
            status=status,
            checked_at=checked_at,
            providers=providers,
            features=features,
            detail=str(payload.get("detail")) if payload.get("detail") else None,
        )


def as_dict(snapshot: NotificationsHealthSnapshot) -> MutableMapping[str, Any]:
    """Render a snapshot into a JSON-serializable mapping."""

    payload: MutableMapping[str, Any] = {
        "module": snapshot.module,
        "version": snapshot.version,
        "status": snapshot.status,
        "checked_at": snapshot.checked_at.isoformat(),
        "providers": {
            provider.name: {
                "name": provider.name,
                "enabled": provider.enabled,
                "handler_registered": provider.handler_registered,
                "metadata": dict(provider.metadata),
            }
            for provider in snapshot.providers
        },
        "features": list(snapshot.features),
    }

    if snapshot.detail:
        payload["detail"] = snapshot.detail

    return payload


__all__ = [
    "NotificationProviderSnapshot",
    "NotificationsHealthSnapshot",
    "as_dict",
]
