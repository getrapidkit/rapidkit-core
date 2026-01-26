"""Override contracts for Api Keys."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from core.services.override_contracts import ConfigurableOverrideMixin

DEFAULTS_KEY = "api_keys_defaults"
TRUTHY_VALUES = {"1", "true", "yes", "on"}
FALSY_VALUES = {"0", "false", "no", "off"}


@dataclass(frozen=True)
class ApiKeysOverrideState:
    """Snapshot of environment-driven overrides for Api Keys defaults."""

    default_scopes: Optional[tuple[str, ...]] = None
    allowed_scopes: Optional[tuple[str, ...]] = None
    rotation_days: Optional[int] = None
    ttl_hours: Optional[int] = None
    max_active_per_owner: Optional[int] = None
    leak_window_hours: Optional[int] = None
    persist_last_used: Optional[bool] = None
    audit_trail: Optional[bool] = None
    repository_backend: Optional[str] = None
    features: Optional[tuple[str, ...]] = None
    pepper_env: Optional[str] = None
    extra_snippet_source: Optional[Path] = None
    extra_snippet_destination: Optional[Path] = None
    extra_snippet_variants: Optional[tuple[str, ...]] = None


def _get_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _parse_bool(name: str) -> Optional[bool]:
    value = _get_env(name)
    if value is None:
        return None
    lowered = value.lower()
    if lowered in TRUTHY_VALUES:
        return True
    if lowered in FALSY_VALUES:
        return False
    return None


def _parse_int(name: str) -> Optional[int]:
    value = _get_env(name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_list(name: str) -> Optional[tuple[str, ...]]:
    value = _get_env(name)
    if value is None:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = value

    items: list[str] = []
    if isinstance(parsed, str):
        items = [segment.strip() for segment in parsed.split(",") if segment.strip()]
    elif isinstance(parsed, (list, tuple)):
        items = [str(segment).strip() for segment in parsed if str(segment).strip()]

    deduped = list(dict.fromkeys(items))
    return tuple(deduped) or None


def _parse_variants(name: str) -> Optional[tuple[str, ...]]:
    variants = _parse_list(name)
    return variants


def resolve_override_state(module_root: Path) -> ApiKeysOverrideState:
    extra_snippet_source: Optional[Path] = None
    extra_snippet_env = _get_env("RAPIDKIT_API_KEYS_EXTRA_SNIPPET")
    if extra_snippet_env:
        candidate = Path(extra_snippet_env)
        if not candidate.is_absolute():
            candidate = module_root / candidate
        extra_snippet_source = candidate

    extra_destination: Optional[Path] = None
    extra_destination_env = _get_env("RAPIDKIT_API_KEYS_EXTRA_SNIPPET_DEST")
    if extra_destination_env:
        extra_destination = Path(extra_destination_env)

    extra_variants = _parse_variants("RAPIDKIT_API_KEYS_EXTRA_SNIPPET_VARIANTS")

    return ApiKeysOverrideState(
        default_scopes=_parse_list("RAPIDKIT_API_KEYS_DEFAULT_SCOPES"),
        allowed_scopes=_parse_list("RAPIDKIT_API_KEYS_ALLOWED_SCOPES"),
        rotation_days=_parse_int("RAPIDKIT_API_KEYS_ROTATION_DAYS"),
        ttl_hours=_parse_int("RAPIDKIT_API_KEYS_TTL_HOURS"),
        max_active_per_owner=_parse_int("RAPIDKIT_API_KEYS_MAX_ACTIVE"),
        leak_window_hours=_parse_int("RAPIDKIT_API_KEYS_LEAK_WINDOW"),
        persist_last_used=_parse_bool("RAPIDKIT_API_KEYS_PERSIST_LAST_USED"),
        audit_trail=_parse_bool("RAPIDKIT_API_KEYS_AUDIT_TRAIL"),
        repository_backend=_get_env("RAPIDKIT_API_KEYS_REPOSITORY"),
        features=_parse_list("RAPIDKIT_API_KEYS_FEATURES"),
        pepper_env=_get_env("RAPIDKIT_API_KEYS_PEPPER_ENV"),
        extra_snippet_source=extra_snippet_source,
        extra_snippet_destination=extra_destination,
        extra_snippet_variants=extra_variants,
    )


def _mutate_defaults(defaults: Mapping[str, Any], state: ApiKeysOverrideState) -> dict[str, Any]:
    mutated = dict(defaults)
    if state.default_scopes is not None:
        mutated["default_scopes"] = list(state.default_scopes)
    if state.allowed_scopes is not None:
        mutated["allowed_scopes"] = list(state.allowed_scopes)
    if state.rotation_days is not None:
        mutated["rotation_days"] = max(state.rotation_days, 0)
    if state.ttl_hours is not None:
        mutated["ttl_hours"] = max(state.ttl_hours, 0)
    if state.max_active_per_owner is not None:
        mutated["max_active_per_owner"] = max(state.max_active_per_owner, 0)
    if state.leak_window_hours is not None:
        mutated["leak_window_hours"] = max(state.leak_window_hours, 0)
    if state.persist_last_used is not None:
        mutated["persist_last_used"] = state.persist_last_used
    if state.audit_trail is not None:
        mutated["audit_trail"] = state.audit_trail
    if state.repository_backend is not None:
        mutated["repository_backend"] = state.repository_backend
    if state.features is not None:
        mutated["features"] = list(state.features)
    if state.pepper_env is not None:
        mutated["pepper_env"] = state.pepper_env
    return mutated


class ApiKeysOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Api Keys."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        self.state = resolve_override_state(self.module_root)
        super().__init__()

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        mutated = dict(context)
        defaults = context.get(DEFAULTS_KEY, {})
        mutated[DEFAULTS_KEY] = _mutate_defaults(defaults, self.state)
        return mutated

    def apply_variant_context_pre(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:  # noqa: ARG002
        return self.apply_base_context(context)

    def apply_variant_context_post(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:  # noqa: ARG002
        return self.apply_base_context(context)

    def post_variant_generation(
        self,
        *,
        variant_name: str,
        target_dir: Path,
        enriched_context: Mapping[str, Any],
    ) -> None:  # noqa: ARG002
        source = self.state.extra_snippet_source
        if source is None:
            return

        if not source.exists():
            raise FileNotFoundError(f"Api Keys override snippet '{source}' does not exist.")

        variants = self.state.extra_snippet_variants
        if variants and variant_name not in variants:
            return

        destination = self.state.extra_snippet_destination or Path("extras") / source.name
        target_path = target_dir / destination
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target_path)


__all__ = ["ApiKeysOverrides", "ApiKeysOverrideState", "resolve_override_state"]
