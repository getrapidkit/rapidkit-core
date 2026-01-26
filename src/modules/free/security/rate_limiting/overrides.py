"""Override contracts for Rate Limiting."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from core.services.override_contracts import ConfigurableOverrideMixin

TRUTHY_VALUES = {"1", "true", "yes", "on"}
FALSY_VALUES = {"0", "false", "no", "off"}


@dataclass(frozen=True)
class RateLimitingOverrideState:
    """Snapshot of environment-driven overrides for rate limiting defaults."""

    backend: Optional[str] = None
    redis_url: Optional[str] = None
    default_limit: Optional[int] = None
    default_window: Optional[int] = None
    default_scope: Optional[str] = None
    default_priority: Optional[int] = None
    default_block_seconds: Optional[int] = None
    trust_forwarded_for: Optional[bool] = None
    forwarded_for_header: Optional[str] = None
    identity_header: Optional[str] = None
    rules: tuple[dict[str, Any], ...] = ()
    metadata: Optional[Mapping[str, Any]] = None


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


def _parse_json_rules(name: str) -> tuple[dict[str, Any], ...]:
    raw = _get_env(name)
    if not raw:
        return ()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return ()
    rules: list[dict[str, Any]] = []
    if isinstance(payload, Mapping):
        payload = [payload]
    if isinstance(payload, list):
        for entry in payload:
            if isinstance(entry, Mapping):
                rules.append(dict(entry))
    return tuple(rules)


def _parse_json_mapping(name: str) -> dict[str, Any]:
    raw = _get_env(name)
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if isinstance(payload, Mapping):
        return dict(payload)
    return {}


def resolve_override_state(_module_root: Path) -> RateLimitingOverrideState:
    return RateLimitingOverrideState(
        backend=_get_env("RAPIDKIT_RATE_LIMIT_BACKEND"),
        redis_url=_get_env("RAPIDKIT_RATE_LIMIT_REDIS_URL"),
        default_limit=_parse_int("RAPIDKIT_RATE_LIMIT_DEFAULT_LIMIT"),
        default_window=_parse_int("RAPIDKIT_RATE_LIMIT_DEFAULT_WINDOW"),
        default_scope=_get_env("RAPIDKIT_RATE_LIMIT_DEFAULT_SCOPE"),
        default_priority=_parse_int("RAPIDKIT_RATE_LIMIT_DEFAULT_PRIORITY"),
        default_block_seconds=_parse_int("RAPIDKIT_RATE_LIMIT_DEFAULT_BLOCK_SECONDS"),
        trust_forwarded_for=_parse_bool("RAPIDKIT_RATE_LIMIT_TRUST_FORWARDED_FOR"),
        forwarded_for_header=_get_env("RAPIDKIT_RATE_LIMIT_FORWARDED_FOR_HEADER"),
        identity_header=_get_env("RAPIDKIT_RATE_LIMIT_IDENTITY_HEADER"),
        rules=_parse_json_rules("RAPIDKIT_RATE_LIMIT_EXTRA_RULES"),
        metadata=_parse_json_mapping("RAPIDKIT_RATE_LIMIT_METADATA") or None,
    )


def _merge_rules(
    existing: list[dict[str, Any]], extra: tuple[dict[str, Any], ...]
) -> list[dict[str, Any]]:
    merged = {rule.get("name", f"rule-{idx}"): dict(rule) for idx, rule in enumerate(existing)}
    for idx, rule in enumerate(extra, start=len(merged)):
        name = rule.get("name")
        key = str(name) if name else f"override-{idx}"
        merged[key] = dict(rule)
    return list(merged.values())


class RateLimitingOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Rate Limiting."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        self.state = resolve_override_state(self.module_root)
        super().__init__()

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        mutated = dict(context)
        defaults = dict(mutated.get("rate_limiting_defaults", {}))
        state = self.state

        if state.backend:
            defaults["backend"] = state.backend
        if state.redis_url is not None:
            defaults["redis_url"] = state.redis_url
        if state.default_limit is not None:
            defaults["default_limit"] = max(state.default_limit, 1)
        if state.default_window is not None:
            defaults["default_window"] = max(state.default_window, 1)
        if state.default_scope:
            defaults["default_scope"] = state.default_scope
        if state.default_priority is not None:
            defaults["default_priority"] = max(state.default_priority, 0)
        if state.default_block_seconds is not None:
            defaults["default_block_seconds"] = max(state.default_block_seconds, 0)
        if state.trust_forwarded_for is not None:
            defaults["trust_forwarded_for"] = state.trust_forwarded_for
        if state.forwarded_for_header:
            defaults["forwarded_for_header"] = state.forwarded_for_header
        if state.identity_header:
            defaults["identity_header"] = state.identity_header
        if state.rules:
            existing_rules = defaults.get("rules")
            if not isinstance(existing_rules, list):
                existing_rules = []
            defaults["rules"] = _merge_rules(
                [dict(rule) for rule in existing_rules if isinstance(rule, Mapping)],
                state.rules,
            )
        if state.metadata:
            metadata = dict(defaults.get("metadata", {}))
            metadata.update(state.metadata)
            defaults["metadata"] = metadata

        mutated["rate_limiting_defaults"] = defaults
        mutated.setdefault("override_metadata", {})
        mutated["override_metadata"].update(
            {
                "rate_limiting_env": True,
                "override_rules": bool(state.rules),
            }
        )
        return mutated

    def apply_variant_context_pre(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:
        mutated = dict(context)
        mutated.setdefault("override_state", self.state)
        mutated.setdefault("framework", variant_name)
        return mutated

    def apply_variant_context_post(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:  # noqa: ARG002
        return dict(context)

    def post_variant_generation(
        self,
        *,
        variant_name: str,
        target_dir: Path,
        enriched_context: Mapping[str, Any],
    ) -> None:  # noqa: ARG002
        return None


__all__ = [
    "RateLimitingOverrides",
    "RateLimitingOverrideState",
    "resolve_override_state",
]
