"""Override contracts for the CORS module."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple

from core.services.override_contracts import ConfigurableOverrideMixin

TRUTHY_VALUES = {"1", "true", "yes", "on"}
FALSY_VALUES = {"0", "false", "no", "off"}


@dataclass(frozen=True)
class CorsOverrideState:
    """Snapshot of environment-driven overrides for CORS defaults."""

    enabled: Optional[bool] = None
    allow_origins: Tuple[str, ...] = ()
    allow_credentials: Optional[bool] = None
    allow_methods: Tuple[str, ...] = ()
    allow_headers: Tuple[str, ...] = ()
    expose_headers: Tuple[str, ...] = ()
    max_age: Optional[int] = None
    log_level: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


def _get_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _parse_bool(name: str) -> Optional[bool]:
    raw = _get_env(name)
    if raw is None:
        return None
    lowered = raw.lower()
    if lowered in TRUTHY_VALUES:
        return True
    if lowered in FALSY_VALUES:
        return False
    return None


def _parse_int(name: str) -> Optional[int]:
    raw = _get_env(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _parse_sequence(name: str) -> Tuple[str, ...]:
    raw = _get_env(name)
    if not raw:
        return ()
    if raw.startswith("["):
        try:
            resolved = json.loads(raw)
        except json.JSONDecodeError:
            resolved = None
        if isinstance(resolved, (list, tuple)):
            return tuple(str(item).strip() for item in resolved if str(item).strip())
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _parse_mapping(name: str) -> Optional[dict[str, Any]]:
    raw = _get_env(name)
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict):
        return {str(key): value for key, value in payload.items()}
    return None


def resolve_override_state(_: Path) -> CorsOverrideState:
    prefix = "RAPIDKIT_CORS"
    return CorsOverrideState(
        enabled=_parse_bool(f"{prefix}_ENABLED"),
        allow_origins=_parse_sequence(f"{prefix}_ALLOW_ORIGINS"),
        allow_credentials=_parse_bool(f"{prefix}_ALLOW_CREDENTIALS"),
        allow_methods=_parse_sequence(f"{prefix}_ALLOW_METHODS"),
        allow_headers=_parse_sequence(f"{prefix}_ALLOW_HEADERS"),
        expose_headers=_parse_sequence(f"{prefix}_EXPOSE_HEADERS"),
        max_age=_parse_int(f"{prefix}_MAX_AGE"),
        log_level=_get_env(f"{prefix}_LOG_LEVEL"),
        metadata=_parse_mapping(f"{prefix}_METADATA"),
    )


def _mutate_defaults(defaults: Mapping[str, Any], state: CorsOverrideState) -> dict[str, Any]:
    mutated = dict(defaults)
    if state.enabled is not None:
        mutated["enabled"] = state.enabled
    if state.allow_origins:
        mutated["allow_origins"] = list(state.allow_origins)
    if state.allow_credentials is not None:
        mutated["allow_credentials"] = state.allow_credentials
    if state.allow_methods:
        mutated["allow_methods"] = list(state.allow_methods)
    if state.allow_headers:
        mutated["allow_headers"] = list(state.allow_headers)
    if state.expose_headers:
        mutated["expose_headers"] = list(state.expose_headers)
    if state.max_age is not None:
        mutated["max_age"] = max(state.max_age, 0)
    if state.log_level:
        mutated["log_level"] = state.log_level
    if state.metadata:
        metadata = dict(mutated.get("metadata", {}))
        metadata.update(state.metadata)
        mutated["metadata"] = metadata
    return mutated


class CorsOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for the CORS module."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        self.state = resolve_override_state(self.module_root)
        super().__init__()

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        mutated = dict(context)
        defaults = mutated.get("cors_defaults", {})
        if not isinstance(defaults, Mapping):
            defaults = {}
        mutated_defaults = _mutate_defaults(defaults, self.state)
        mutated["cors_defaults"] = mutated_defaults
        mutated.setdefault("override_metadata", {})
        mutated["override_metadata"].update(
            {
                "cors_env_overrides": True,
                "cors_sequence_overrides": bool(
                    self.state.allow_origins
                    or self.state.allow_methods
                    or self.state.allow_headers
                    or self.state.expose_headers
                ),
                "cors_metadata_overrides": bool(self.state.metadata),
                "cors_log_level_override": bool(self.state.log_level),
            }
        )
        mutated["cors_override_state"] = self.state
        return mutated

    def apply_variant_context_pre(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:
        enriched = dict(context)
        enriched.setdefault("framework", variant_name)
        enriched.setdefault("cors_override_state", self.state)
        return enriched

    def apply_variant_context_post(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:
        _ = variant_name  # Deliberately unused yet retained for future parity hooks.
        return dict(context)

    def post_variant_generation(
        self,
        *,
        variant_name: str,
        target_dir: Path,
        enriched_context: Mapping[str, Any],
    ) -> None:
        _ = (variant_name, target_dir, enriched_context)
        # Reserved for future hooks (e.g., documentation injection).


__all__ = ["CorsOverrides", "CorsOverrideState", "resolve_override_state"]
