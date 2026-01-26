"""Typed helpers for Rate Limiting module metadata serialization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping, Sequence


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return default


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_str(value: Any, default: str | None = None) -> str | None:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _coerce_sequence(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        cleaned = value.strip()
        return (cleaned,) if cleaned else ()
    if isinstance(value, Sequence):
        return tuple(str(item).strip() for item in value if isinstance(item, str) and item.strip())
    return ()


@dataclass(frozen=True)
class RateLimitRuleSnapshot:
    """Declarative view of a configured rate limiting rule."""

    name: str
    limit: int
    window_seconds: int
    scope: str
    priority: int
    routes: tuple[str, ...]
    methods: tuple[str, ...]

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any] | None,
        *,
        fallback_name: str = "rule",
        fallback_priority: int = 0,
    ) -> "RateLimitRuleSnapshot":
        data = payload or {}
        name = _coerce_str(data.get("name"), fallback_name) or fallback_name
        limit = max(_coerce_int(data.get("limit"), 0), 0)
        window_seconds = max(
            _coerce_int(data.get("window_seconds", data.get("window")), 0),
            0,
        )
        scope = _coerce_str(data.get("scope"), "identity") or "identity"
        priority = _coerce_int(data.get("priority"), fallback_priority)
        routes = _coerce_sequence(data.get("routes"))
        methods = tuple(item.upper() for item in _coerce_sequence(data.get("methods")))
        return cls(
            name=name,
            limit=limit,
            window_seconds=window_seconds,
            scope=scope,
            priority=priority,
            routes=routes,
            methods=methods,
        )

    def as_dict(self) -> MutableMapping[str, Any]:
        return {
            "name": self.name,
            "limit": self.limit,
            "window_seconds": self.window_seconds,
            "scope": self.scope,
            "priority": self.priority,
            "routes": list(self.routes),
            "methods": list(self.methods),
        }


@dataclass(frozen=True)
class RateLimiterHealthSnapshot:
    """Normalized metadata payload describing rate limiting state."""

    module: str
    status: str
    checked_at: datetime
    enabled: bool
    backend: str | None
    default_rule: RateLimitRuleSnapshot
    rules: tuple[RateLimitRuleSnapshot, ...]
    features: tuple[str, ...]
    detail: str | None = None

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any] | None,
        *,
        module_name: str,
        features: Sequence[str],
        detail: str | None = None,
    ) -> "RateLimiterHealthSnapshot":
        data = payload or {}
        metadata = data if "enabled" in data else data.get("metadata", {})
        if not isinstance(metadata, Mapping):
            metadata = {}

        enabled = _coerce_bool(metadata.get("enabled"), True)
        backend = _coerce_str(metadata.get("backend"))
        default_rule = RateLimitRuleSnapshot.from_mapping(
            metadata.get("default_rule"),
            fallback_name="default",
            fallback_priority=0,
        )
        rules_payload = metadata.get("rules")
        rules: tuple[RateLimitRuleSnapshot, ...]
        if isinstance(rules_payload, Sequence):
            rules = tuple(
                RateLimitRuleSnapshot.from_mapping(item, fallback_name=f"rule-{idx}", fallback_priority=idx)
                for idx, item in enumerate(rules_payload)
                if isinstance(item, Mapping)
            )
        else:
            rules = ()

        status = str(data.get("status") or ("ok" if enabled else "disabled"))
        checked_at_raw = data.get("checked_at")
        if isinstance(checked_at_raw, datetime):
            checked_at = checked_at_raw
        elif checked_at_raw:
            try:
                checked_at = datetime.fromisoformat(str(checked_at_raw))
            except ValueError:
                checked_at = datetime.now(timezone.utc)
        else:
            checked_at = datetime.now(timezone.utc)

        if checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=timezone.utc)

        feature_tuple = tuple(str(item) for item in features if isinstance(item, str))

        return cls(
            module=str(data.get("module", module_name)),
            status=status,
            checked_at=checked_at,
            enabled=enabled,
            backend=backend,
            default_rule=default_rule,
            rules=rules,
            features=feature_tuple,
            detail=detail,
        )


def as_dict(snapshot: RateLimiterHealthSnapshot) -> MutableMapping[str, Any]:
    """Render a snapshot into a JSON-serializable structure."""

    payload: MutableMapping[str, Any] = {
        "module": snapshot.module,
        "status": snapshot.status,
        "checked_at": snapshot.checked_at.isoformat(),
        "enabled": snapshot.enabled,
        "backend": snapshot.backend,
        "default_rule": snapshot.default_rule.as_dict(),
        "rules": [rule.as_dict() for rule in snapshot.rules],
        "features": list(snapshot.features),
    }
    if snapshot.detail:
        payload["detail"] = snapshot.detail
    return payload


__all__ = [
    "RateLimitRuleSnapshot",
    "RateLimiterHealthSnapshot",
    "as_dict",
]
