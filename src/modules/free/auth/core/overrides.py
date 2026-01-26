"""Override contracts for the Auth Core module."""

# pyright: reportMissingImports=false

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from core.services.override_contracts import ConfigurableOverrideMixin


@dataclass(frozen=True)
class AuthCoreOverrideState:
    """Snapshot of environment-driven overrides for Auth Core defaults."""

    hash_name: Optional[str] = None
    iterations: Optional[int] = None
    salt_bytes: Optional[int] = None
    token_bytes: Optional[int] = None
    token_ttl_seconds: Optional[int] = None
    issuer: Optional[str] = None
    pepper_env: Optional[str] = None
    policy: Optional[dict[str, Any]] = None


def _get_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _parse_int(name: str) -> Optional[int]:
    candidate = _get_env(name)
    if candidate is None:
        return None
    try:
        return int(candidate)
    except ValueError:
        return None


def _parse_policy(name: str) -> Optional[dict[str, Any]]:
    raw = _get_env(name)
    if raw is None:
        return None
    try:
        parsed: Any = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return {str(key): value for key, value in parsed.items()}
    return None


def resolve_override_state(_: Path) -> AuthCoreOverrideState:
    return AuthCoreOverrideState(
        hash_name=_get_env("RAPIDKIT_AUTH_CORE_HASH"),
        iterations=_parse_int("RAPIDKIT_AUTH_CORE_ITERATIONS"),
        salt_bytes=_parse_int("RAPIDKIT_AUTH_CORE_SALT_BYTES"),
        token_bytes=_parse_int("RAPIDKIT_AUTH_CORE_TOKEN_BYTES"),
        token_ttl_seconds=_parse_int("RAPIDKIT_AUTH_CORE_TOKEN_TTL"),
        issuer=_get_env("RAPIDKIT_AUTH_CORE_ISSUER"),
        pepper_env=_get_env("RAPIDKIT_AUTH_CORE_PEPPER_ENV"),
        policy=_parse_policy("RAPIDKIT_AUTH_CORE_POLICY"),
    )


def _mutate_defaults(defaults: Mapping[str, Any], state: AuthCoreOverrideState) -> dict[str, Any]:
    mutated = dict(defaults)
    if state.hash_name:
        mutated["hash_name"] = state.hash_name
    if state.iterations is not None:
        mutated["iterations"] = max(state.iterations, 1)
    if state.salt_bytes is not None:
        mutated["salt_bytes"] = max(state.salt_bytes, 8)
    if state.token_bytes is not None:
        mutated["token_bytes"] = max(state.token_bytes, 8)
    if state.token_ttl_seconds is not None:
        mutated["token_ttl_seconds"] = max(state.token_ttl_seconds, 60)
    if state.pepper_env:
        mutated["pepper_env"] = state.pepper_env
    if state.issuer:
        mutated["issuer"] = state.issuer
    if state.policy:
        policy = dict(mutated.get("policy", {}))
        policy.update(state.policy)
        mutated["policy"] = policy
    return mutated


class AuthCoreOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Auth Core."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        self.state = resolve_override_state(self.module_root)
        super().__init__()

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        mutated = dict(context)
        defaults = context.get("auth_core_defaults", {})
        mutated["auth_core_defaults"] = _mutate_defaults(defaults, self.state)
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
        # No post-generation hooks required at this stage. Hook retained for future use.
        return None


__all__ = [
    "AuthCoreOverrides",
    "AuthCoreOverrideState",
    "resolve_override_state",
]
