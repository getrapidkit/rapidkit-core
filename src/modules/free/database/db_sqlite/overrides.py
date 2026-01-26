"""Override contracts for Db Sqlite."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from core.services.override_contracts import ConfigurableOverrideMixin

ENV_PREFIX = "RAPIDKIT_DB_SQLITE_"


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
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
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


def _parse_mapping(name: str) -> Optional[dict[str, str]]:
    value = _get_env(name)
    if value is None:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = value

    if isinstance(parsed, Mapping):
        return {str(key): str(val) for key, val in parsed.items()}

    if isinstance(parsed, str):
        mapping: dict[str, str] = {}
        for segment in parsed.split(","):
            if "=" not in segment:
                continue
            key, raw_value = segment.split("=", 1)
            key = key.strip()
            if not key:
                continue
            mapping[key] = raw_value.strip()
        if mapping:
            return mapping
    return None


@dataclass(frozen=True)
class DbSqliteOverrideState:
    """Snapshot of override configuration resolved from the environment."""

    database_path: Optional[str] = None
    create_if_missing: Optional[bool] = None
    timeout_seconds: Optional[float] = None
    pool_max_size: Optional[int] = None
    pool_recycle_seconds: Optional[int] = None
    pragmas: Optional[dict[str, str]] = None


def resolve_override_state(
    _module_root: Path | None = None,
) -> DbSqliteOverrideState:
    """Resolve override values from environment variables."""

    return DbSqliteOverrideState(
        database_path=_get_env(f"{ENV_PREFIX}PATH"),
        create_if_missing=_parse_bool(f"{ENV_PREFIX}CREATE_IF_MISSING"),
        timeout_seconds=_parse_float(f"{ENV_PREFIX}TIMEOUT_SECONDS"),
        pool_max_size=_parse_int(f"{ENV_PREFIX}POOL_MAX_SIZE"),
        pool_recycle_seconds=_parse_int(f"{ENV_PREFIX}POOL_RECYCLE_SECONDS"),
        pragmas=_parse_mapping(f"{ENV_PREFIX}PRAGMAS"),
    )


class DbSqliteOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Db Sqlite."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        self.state = resolve_override_state(self.module_root)
        super().__init__()

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        mutated = dict(context)

        default_database_path = self.state.database_path
        if default_database_path:
            mutated["default_database_path"] = default_database_path

        pool_config = dict(mutated.get("default_pool", {}))
        if self.state.pool_max_size is not None:
            pool_config["max_size"] = max(self.state.pool_max_size, 1)
        if self.state.pool_recycle_seconds is not None:
            pool_config["recycle_seconds"] = max(self.state.pool_recycle_seconds, 0)
        mutated["default_pool"] = pool_config

        if self.state.timeout_seconds is not None:
            mutated["default_timeout_seconds"] = max(self.state.timeout_seconds, 0.0)

        if self.state.pragmas:
            default_pragmas = dict(mutated.get("default_pragmas", {}))
            default_pragmas.update(self.state.pragmas)
            mutated["default_pragmas"] = default_pragmas

        if self.state.create_if_missing is not None:
            mutated["default_create_if_missing"] = self.state.create_if_missing

        return mutated

    def apply_variant_context_pre(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:  # noqa: ARG002
        return self.apply_base_context(context)

    def apply_variant_context_post(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:  # noqa: ARG002
        return self.apply_base_context(context)

    def post_variant_generation(
        self,
        *,
        variant_name: str,
        target_dir: Path,
        enriched_context: Mapping[str, Any],
    ) -> None:  # noqa: ARG002
        if not variant_name.startswith("nestjs"):
            return

        from .frameworks.nestjs import NestJSPlugin

        NestJSPlugin()._ensure_package_dependencies(target_dir / "package.json")
        return


__all__ = [
    "DbSqliteOverrides",
    "DbSqliteOverrideState",
    "resolve_override_state",
]
