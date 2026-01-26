"""Override contracts for Users Profiles."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from core.services.override_contracts import ConfigurableOverrideMixin


@dataclass(frozen=True)
class UsersProfileOverrideState:
    """Environment-driven overrides for Users Profiles defaults."""

    default_timezone: Optional[str] = None
    max_bio_length: Optional[int] = None
    avatar_max_bytes: Optional[int] = None
    allow_marketing_opt_in: Optional[bool] = None
    social_links_limit: Optional[int] = None
    default_visibility: Optional[str] = None
    supported_visibilities: Optional[tuple[str, ...]] = None


def _get_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _parse_bool(name: str) -> Optional[bool]:
    raw = _get_env(name)
    if raw is None:
        return None
    lowered = raw.lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return None


def _parse_int(
    name: str, *, minimum: int | None = None, maximum: int | None = None
) -> Optional[int]:
    raw = _get_env(name)
    if raw is None:
        return None
    try:
        parsed = int(raw, 10)
    except ValueError:
        return None
    if minimum is not None:
        parsed = max(parsed, minimum)
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed


def _parse_sequence(name: str) -> Optional[tuple[str, ...]]:
    raw = _get_env(name)
    if raw is None:
        return None
    items: Sequence[str] = (
        [item.strip() for item in raw.split(",")] if "," in raw else [raw.strip()]
    )
    normalized = tuple(item for item in items if item)
    return normalized or None


def resolve_override_state(_: Path) -> UsersProfileOverrideState:
    prefix = "RAPIDKIT_USERS_PROFILES"
    return UsersProfileOverrideState(
        default_timezone=_get_env(f"{prefix}_DEFAULT_TIMEZONE"),
        max_bio_length=_parse_int(f"{prefix}_MAX_BIO_LENGTH", minimum=50, maximum=1000),
        avatar_max_bytes=_parse_int(f"{prefix}_AVATAR_MAX_BYTES", minimum=10_000),
        allow_marketing_opt_in=_parse_bool(f"{prefix}_ALLOW_MARKETING_OPT_IN"),
        social_links_limit=_parse_int(f"{prefix}_SOCIAL_LINKS_LIMIT", minimum=0, maximum=10),
        default_visibility=_get_env(f"{prefix}_DEFAULT_VISIBILITY"),
        supported_visibilities=_parse_sequence(f"{prefix}_SUPPORTED_VISIBILITIES"),
    )


def _mutate_defaults(
    defaults: Mapping[str, Any], state: UsersProfileOverrideState
) -> dict[str, Any]:
    mutated = dict(defaults)
    if state.default_timezone:
        mutated["default_timezone"] = state.default_timezone
    if state.max_bio_length is not None:
        mutated["max_bio_length"] = state.max_bio_length
    if state.avatar_max_bytes is not None:
        mutated["avatar_max_bytes"] = state.avatar_max_bytes
    if state.allow_marketing_opt_in is not None:
        mutated["allow_marketing_opt_in"] = state.allow_marketing_opt_in
    if state.social_links_limit is not None:
        mutated["social_links_limit"] = state.social_links_limit
    if state.default_visibility:
        mutated["default_visibility"] = state.default_visibility
    if state.supported_visibilities:
        mutated["supported_visibilities"] = list(state.supported_visibilities)
    return mutated


class UsersProfileOverrides(ConfigurableOverrideMixin):
    """Extend or customise generated behaviour for Users Profiles."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        self.state = resolve_override_state(self.module_root)
        super().__init__()

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        mutated = dict(context)
        defaults = context.get("users_profiles_defaults", {})
        mutated["users_profiles_defaults"] = _mutate_defaults(defaults, self.state)
        return mutated

    def apply_variant_context_pre(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:  # noqa: ARG002
        return self.apply_base_context(context)

    def apply_variant_context_post(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:  # noqa: ARG002
        enriched = self.apply_base_context(context)
        enriched.setdefault("users_profiles_defaults", context.get("users_profiles_defaults", {}))
        return enriched

    def post_variant_generation(
        self,
        *,
        variant_name: str,
        target_dir: Path,
        enriched_context: Mapping[str, Any],
    ) -> None:  # noqa: ARG002
        return None


__all__ = [
    "UsersProfileOverrides",
    "UsersProfileOverrideState",
    "resolve_override_state",
]
