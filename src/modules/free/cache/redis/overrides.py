"""Override contracts for Redis."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from core.services.override_contracts import ConfigurableOverrideMixin

TRUTHY_VALUES = {"1", "true", "yes", "on"}
FALSY_VALUES = {"0", "false", "no", "off"}


@dataclass(frozen=True)
class RedisOverrideState:
    """Snapshot of environment-driven overrides for Redis defaults."""

    url: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    db: Optional[int] = None
    password: Optional[str] = None
    use_tls: Optional[bool] = None
    preconnect: Optional[bool] = None
    connect_retries: Optional[int] = None
    connect_backoff_base: Optional[float] = None
    cache_ttl: Optional[int] = None
    project_name: Optional[str] = None
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


def _parse_float(name: str) -> Optional[float]:
    value = _get_env(name)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_json_tuple(name: str) -> Optional[tuple[str, ...]]:
    value = _get_env(name)
    if value is None:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, list):
        variants = tuple(str(item).strip() for item in parsed if str(item).strip())
        return variants or None
    if isinstance(parsed, str) and parsed.strip():
        return (parsed.strip(),)
    return None


def resolve_override_state(module_root: Path) -> RedisOverrideState:
    extra_snippet_source: Optional[Path] = None
    extra_snippet_env = _get_env("RAPIDKIT_REDIS_EXTRA_SNIPPET")
    if extra_snippet_env:
        candidate = Path(extra_snippet_env)
        if not candidate.is_absolute():
            candidate = module_root / candidate
        extra_snippet_source = candidate

    extra_destination: Optional[Path] = None
    extra_destination_env = _get_env("RAPIDKIT_REDIS_EXTRA_SNIPPET_DEST")
    if extra_destination_env:
        extra_destination = Path(extra_destination_env)

    extra_variants = _parse_json_tuple("RAPIDKIT_REDIS_EXTRA_SNIPPET_VARIANTS")

    return RedisOverrideState(
        url=_get_env("RAPIDKIT_REDIS_FORCE_URL"),
        host=_get_env("RAPIDKIT_REDIS_FORCE_HOST"),
        port=_parse_int("RAPIDKIT_REDIS_FORCE_PORT"),
        db=_parse_int("RAPIDKIT_REDIS_FORCE_DB"),
        password=_get_env("RAPIDKIT_REDIS_FORCE_PASSWORD"),
        use_tls=_parse_bool("RAPIDKIT_REDIS_FORCE_TLS"),
        preconnect=_parse_bool("RAPIDKIT_REDIS_FORCE_PRECONNECT"),
        connect_retries=_parse_int("RAPIDKIT_REDIS_FORCE_RETRIES"),
        connect_backoff_base=_parse_float("RAPIDKIT_REDIS_FORCE_BACKOFF"),
        cache_ttl=_parse_int("RAPIDKIT_REDIS_FORCE_TTL"),
        project_name=_get_env("RAPIDKIT_REDIS_PROJECT_NAME"),
        extra_snippet_source=extra_snippet_source,
        extra_snippet_destination=extra_destination,
        extra_snippet_variants=extra_variants,
    )


def _mutate_defaults(defaults: Mapping[str, Any], state: RedisOverrideState) -> dict[str, Any]:
    mutated = dict(defaults)
    if state.url:
        mutated["url"] = state.url
    if state.host:
        mutated["host"] = state.host
    if state.port is not None:
        mutated["port"] = state.port
    if state.db is not None:
        mutated["db"] = state.db
    if state.password is not None:
        mutated["password"] = state.password
    if state.use_tls is not None:
        mutated["use_tls"] = state.use_tls
    if state.preconnect is not None:
        mutated["preconnect"] = state.preconnect
    if state.connect_retries is not None:
        mutated["connect_retries"] = max(state.connect_retries, 0)
    if state.connect_backoff_base is not None:
        mutated["connect_backoff_base"] = max(state.connect_backoff_base, 0.0)
    if state.cache_ttl is not None:
        mutated["cache_ttl"] = max(state.cache_ttl, 0)
    return mutated


class RedisOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Redis."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        self.state = resolve_override_state(self.module_root)
        super().__init__()

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        mutated = dict(context)
        defaults = context.get("redis_defaults", {})
        mutated["redis_defaults"] = _mutate_defaults(defaults, self.state)
        if self.state.project_name:
            mutated["project_name"] = self.state.project_name
            mutated["project_slug"] = self.state.project_name.lower().replace(" ", "-")
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
            raise FileNotFoundError(f"Redis override snippet '{source}' does not exist.")

        variants = self.state.extra_snippet_variants
        if variants and variant_name not in variants:
            return

        destination = self.state.extra_snippet_destination or Path("extras") / source.name
        target_path = target_dir / destination
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target_path)


__all__ = [
    "RedisOverrides",
    "RedisOverrideState",
    "resolve_override_state",
]
