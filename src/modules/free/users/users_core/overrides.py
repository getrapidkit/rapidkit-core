"""Override contracts for Users Core."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from core.services.override_contracts import ConfigurableOverrideMixin


@dataclass(frozen=True)
class UsersCoreOverrideState:
    """Environment-driven overrides for Users Core defaults."""

    allow_registration: Optional[bool] = None
    enforce_unique_email: Optional[bool] = None
    default_locale: Optional[str] = None
    audit_log_enabled: Optional[bool] = None
    max_results_per_page: Optional[int] = None
    passwordless_supported: Optional[bool] = None
    supported_locales: Optional[tuple[str, ...]] = None


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


def _parse_int(name: str, *, minimum: int = 1) -> Optional[int]:
    raw = _get_env(name)
    if raw is None:
        return None
    try:
        parsed = int(raw, 10)
    except ValueError:
        return None
    return max(parsed, minimum)


def _parse_sequence(name: str) -> Optional[tuple[str, ...]]:
    raw = _get_env(name)
    if raw is None:
        return None
    items: Sequence[str] = (
        [item.strip() for item in raw.split(",")] if "," in raw else [raw.strip()]
    )
    normalized = tuple(item for item in items if item)
    return normalized or None


def resolve_override_state(_: Path) -> UsersCoreOverrideState:
    prefix = "RAPIDKIT_USERS_CORE"
    return UsersCoreOverrideState(
        allow_registration=_parse_bool(f"{prefix}_ALLOW_REGISTRATION"),
        enforce_unique_email=_parse_bool(f"{prefix}_ENFORCE_UNIQUE_EMAIL"),
        default_locale=_get_env(f"{prefix}_DEFAULT_LOCALE"),
        audit_log_enabled=_parse_bool(f"{prefix}_AUDIT_LOG_ENABLED"),
        # Support both the historical env var name and the more descriptive new name.
        # Preference is given to the new name when both are present.
        max_results_per_page=(
            _parse_int(f"{prefix}_MAX_RESULTS_PER_PAGE", minimum=1)
            or _parse_int(f"{prefix}_MAX_RESULTS", minimum=1)
        ),
        passwordless_supported=_parse_bool(f"{prefix}_PASSWORDLESS_SUPPORTED"),
        supported_locales=_parse_sequence(f"{prefix}_SUPPORTED_LOCALES"),
    )


def _mutate_defaults(defaults: Mapping[str, Any], state: UsersCoreOverrideState) -> dict[str, Any]:
    mutated = dict(defaults)
    if state.allow_registration is not None:
        mutated["allow_registration"] = state.allow_registration
    if state.enforce_unique_email is not None:
        mutated["enforce_unique_email"] = state.enforce_unique_email
    if state.default_locale:
        mutated["default_locale"] = state.default_locale
    if state.audit_log_enabled is not None:
        mutated["audit_log_enabled"] = state.audit_log_enabled
    if state.max_results_per_page is not None:
        mutated["max_results_per_page"] = state.max_results_per_page
    if state.passwordless_supported is not None:
        mutated["passwordless_supported"] = state.passwordless_supported
    if state.supported_locales:
        mutated["supported_locales"] = list(state.supported_locales)
    return mutated


class UsersCoreOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Users Core."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        self.state = resolve_override_state(self.module_root)
        super().__init__()

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        mutated = dict(context)
        defaults = context.get("users_core_defaults", {})
        mutated["users_core_defaults"] = _mutate_defaults(defaults, self.state)
        return mutated

    def apply_variant_context_pre(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:  # noqa: ARG002
        return self.apply_base_context(context)

    def apply_variant_context_post(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:  # noqa: ARG002
        enriched = self.apply_base_context(context)
        enriched.setdefault("users_core_defaults", context.get("users_core_defaults", {}))
        return enriched

    def post_variant_generation(
        self,
        *,
        variant_name: str,
        target_dir: Path,
        enriched_context: Mapping[str, Any],
    ) -> None:  # noqa: ARG002
        # Hooks retained for future extension (e.g. writing docs or validation markers).
        return None


__all__ = [
    "UsersCoreOverrides",
    "UsersCoreOverrideState",
    "resolve_override_state",
]
