"""Override contracts for Db Mongo."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from core.services.override_contracts import ConfigurableOverrideMixin

ENV_PREFIX = "RAPIDKIT_DB_MONGO_"


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


def _parse_list(name: str) -> Optional[list[str]]:
    value = _get_env(name)
    if value is None:
        return None
    if value.startswith("[") and value.endswith("]"):
        trimmed = value.strip("[]")
        segments = [
            segment.strip().strip("\"'") for segment in trimmed.split(",") if segment.strip()
        ]
        if segments:
            return segments
        return None
    segments = [segment.strip() for segment in value.split(",") if segment.strip()]
    return segments or None


@dataclass(frozen=True)
class DbMongoOverrideState:
    """Snapshot of override configuration resolved from the environment."""

    connection_uri: Optional[str] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    auth_source: Optional[str] = None
    replica_set: Optional[str] = None
    app_name: Optional[str] = None
    read_preference: Optional[str] = None
    retry_reads: Optional[bool] = None
    retry_writes: Optional[bool] = None
    tls: Optional[bool] = None
    tls_allow_invalid: Optional[bool] = None
    pool_min_size: Optional[int] = None
    pool_max_size: Optional[int] = None
    connect_timeout_ms: Optional[int] = None
    server_selection_timeout_ms: Optional[int] = None
    max_idle_time_ms: Optional[int] = None
    compressors: Optional[list[str]] = None
    health_timeout_ms: Optional[int] = None
    health_metrics_enabled: Optional[bool] = None


def resolve_override_state(module_root: Path | None = None) -> DbMongoOverrideState:  # noqa: ARG001
    """Resolve override values from environment variables."""

    return DbMongoOverrideState(
        connection_uri=_get_env(f"{ENV_PREFIX}URI"),
        database_name=_get_env(f"{ENV_PREFIX}DATABASE"),
        username=_get_env(f"{ENV_PREFIX}USERNAME"),
        password=_get_env(f"{ENV_PREFIX}PASSWORD"),
        auth_source=_get_env(f"{ENV_PREFIX}AUTH_SOURCE"),
        replica_set=_get_env(f"{ENV_PREFIX}REPLICA_SET"),
        app_name=_get_env(f"{ENV_PREFIX}APP_NAME"),
        read_preference=_get_env(f"{ENV_PREFIX}READ_PREFERENCE"),
        retry_reads=_parse_bool(f"{ENV_PREFIX}RETRY_READS"),
        retry_writes=_parse_bool(f"{ENV_PREFIX}RETRY_WRITES"),
        tls=_parse_bool(f"{ENV_PREFIX}TLS"),
        tls_allow_invalid=_parse_bool(f"{ENV_PREFIX}TLS_ALLOW_INVALID_CERTS"),
        pool_min_size=_parse_int(f"{ENV_PREFIX}MIN_POOL_SIZE"),
        pool_max_size=_parse_int(f"{ENV_PREFIX}MAX_POOL_SIZE"),
        connect_timeout_ms=_parse_int(f"{ENV_PREFIX}CONNECT_TIMEOUT_MS"),
        server_selection_timeout_ms=_parse_int(f"{ENV_PREFIX}SERVER_SELECTION_TIMEOUT_MS"),
        max_idle_time_ms=_parse_int(f"{ENV_PREFIX}MAX_IDLE_TIME_MS"),
        compressors=_parse_list(f"{ENV_PREFIX}COMPRESSORS"),
        health_timeout_ms=_parse_int(f"{ENV_PREFIX}HEALTH_TIMEOUT_MS"),
        health_metrics_enabled=_parse_bool(f"{ENV_PREFIX}HEALTH_METRICS"),
    )


class DbMongoOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Db Mongo."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        self.state = resolve_override_state(self.module_root)
        super().__init__()

    def _mutate_defaults(self, mutated: dict[str, Any]) -> None:
        defaults = mutated.setdefault("mongo_defaults", {})

        if self.state.connection_uri:
            mutated["default_connection_uri"] = self.state.connection_uri
            defaults["connection_uri"] = self.state.connection_uri
        if self.state.database_name:
            mutated["default_database_name"] = self.state.database_name
            defaults["database"] = self.state.database_name
        if self.state.username is not None:
            mutated["default_username"] = self.state.username
            defaults["username"] = self.state.username
        if self.state.password is not None:
            mutated["default_password"] = self.state.password
            defaults["password"] = self.state.password
        if self.state.auth_source:
            mutated["default_auth_source"] = self.state.auth_source
            defaults["auth_source"] = self.state.auth_source
        if self.state.replica_set:
            mutated["default_replica_set"] = self.state.replica_set
            defaults["replica_set"] = self.state.replica_set
        if self.state.app_name:
            mutated["default_app_name"] = self.state.app_name
            defaults["app_name"] = self.state.app_name
        if self.state.read_preference:
            mutated["default_read_preference"] = self.state.read_preference
            defaults["read_preference"] = self.state.read_preference
        if self.state.retry_reads is not None:
            mutated["default_retry_reads"] = self.state.retry_reads
            defaults["retry_reads"] = self.state.retry_reads
        if self.state.retry_writes is not None:
            mutated["default_retry_writes"] = self.state.retry_writes
            defaults["retry_writes"] = self.state.retry_writes
        if self.state.tls is not None:
            mutated["default_tls_enabled"] = self.state.tls
            defaults["tls"] = self.state.tls
        if self.state.tls_allow_invalid is not None:
            mutated["default_tls_allow_invalid_certificates"] = self.state.tls_allow_invalid
            defaults["tls_allow_invalid_certificates"] = self.state.tls_allow_invalid
        if self.state.pool_min_size is not None:
            value = max(self.state.pool_min_size, 0)
            mutated["default_pool_min_size"] = value
            defaults["min_pool_size"] = value
        if self.state.pool_max_size is not None:
            value = max(self.state.pool_max_size, 1)
            mutated["default_pool_max_size"] = value
            defaults["max_pool_size"] = value
        if self.state.connect_timeout_ms is not None:
            value = max(self.state.connect_timeout_ms, 0)
            mutated["default_connect_timeout_ms"] = value
            defaults["connect_timeout_ms"] = value
        if self.state.server_selection_timeout_ms is not None:
            value = max(self.state.server_selection_timeout_ms, 0)
            mutated["default_server_selection_timeout_ms"] = value
            defaults["server_selection_timeout_ms"] = value
        if self.state.max_idle_time_ms is not None:
            value = max(self.state.max_idle_time_ms, 0)
            mutated["default_max_idle_time_ms"] = value
            defaults["max_idle_time_ms"] = value
        if self.state.compressors:
            mutated["default_compressors"] = list(self.state.compressors)
            defaults["compressors"] = list(self.state.compressors)
        if self.state.health_timeout_ms is not None:
            value = max(self.state.health_timeout_ms, 1)
            mutated["default_health_timeout_ms"] = value
            mutated.setdefault("health_defaults", {})["ping_timeout_ms"] = value
        if self.state.health_metrics_enabled is not None:
            mutated["default_collect_metrics"] = self.state.health_metrics_enabled
            mutated.setdefault("health_defaults", {})["metrics"] = self.state.health_metrics_enabled

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        mutated = dict(context)
        self._mutate_defaults(mutated)
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
        return None


__all__ = [
    "DbMongoOverrides",
    "DbMongoOverrideState",
    "resolve_override_state",
]
