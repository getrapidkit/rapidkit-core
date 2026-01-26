"""Override contracts for Observability Core."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from core.services.override_contracts import ConfigurableOverrideMixin

DEFAULTS_KEY = "observability_defaults"

TRUTHY_VALUES = {"1", "true", "yes", "on"}
FALSY_VALUES = {"0", "false", "no", "off"}


@dataclass(frozen=True)
class ObservabilityOverrideState:
    """Snapshot of environment-driven overrides for observability defaults."""

    service_name: Optional[str] = None
    environment: Optional[str] = None
    resource_attributes: Optional[dict[str, str]] = None

    metrics_enabled: Optional[bool] = None
    metrics_exporter: Optional[str] = None
    metrics_endpoint: Optional[str] = None
    metrics_namespace: Optional[str] = None
    metrics_labels: Optional[dict[str, str]] = None
    metrics_buckets: Optional[tuple[float, ...]] = None
    metrics_retention: Optional[int] = None
    metrics_process_metrics: Optional[bool] = None

    tracing_enabled: Optional[bool] = None
    tracing_exporter: Optional[str] = None
    tracing_endpoint: Optional[str] = None
    tracing_sample_ratio: Optional[float] = None
    tracing_include_headers: Optional[bool] = None

    logging_level: Optional[str] = None
    logging_structured: Optional[bool] = None
    logging_include_trace_ids: Optional[bool] = None

    events_buffer_size: Optional[int] = None
    events_flush_interval: Optional[int] = None
    events_audit_enabled: Optional[bool] = None
    retry_attempts: Optional[int] = None


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

    mapping: dict[str, str] = {}
    if isinstance(parsed, str):
        for segment in parsed.split(","):
            if "=" not in segment:
                continue
            key, raw_value = segment.split("=", 1)
            key = key.strip()
            if not key:
                continue
            mapping[key] = raw_value.strip()
    return mapping or None


def _parse_float_list(name: str) -> Optional[tuple[float, ...]]:
    value = _get_env(name)
    if value is None:
        return None

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = value

    numbers: list[float] = []
    if isinstance(parsed, (list, tuple)):
        for element in parsed:
            try:
                numbers.append(float(element))
            except (TypeError, ValueError):
                continue
    elif isinstance(parsed, str):
        for raw_chunk in parsed.split(","):
            chunk = raw_chunk.strip()
            if not chunk:
                continue
            try:
                numbers.append(float(chunk))
            except ValueError:
                continue

    deduped = list(dict.fromkeys(numbers))
    return tuple(deduped) or None


def resolve_override_state(
    _module_root: Path | None = None,
) -> ObservabilityOverrideState:
    """Resolve overrides from environment variables."""

    return ObservabilityOverrideState(
        service_name=_get_env("RAPIDKIT_OBSERVABILITY_SERVICE_NAME"),
        environment=_get_env("RAPIDKIT_OBSERVABILITY_ENVIRONMENT"),
        resource_attributes=_parse_mapping("RAPIDKIT_OBSERVABILITY_RESOURCE_ATTRS"),
        metrics_enabled=_parse_bool("RAPIDKIT_OBSERVABILITY_METRICS_ENABLED"),
        metrics_exporter=_get_env("RAPIDKIT_OBSERVABILITY_METRICS_EXPORTER"),
        metrics_endpoint=_get_env("RAPIDKIT_OBSERVABILITY_METRICS_ENDPOINT"),
        metrics_namespace=_get_env("RAPIDKIT_OBSERVABILITY_METRICS_NAMESPACE"),
        metrics_labels=_parse_mapping("RAPIDKIT_OBSERVABILITY_METRICS_LABELS"),
        metrics_buckets=_parse_float_list("RAPIDKIT_OBSERVABILITY_METRICS_BUCKETS"),
        metrics_retention=_parse_int("RAPIDKIT_OBSERVABILITY_METRICS_RETENTION"),
        metrics_process_metrics=_parse_bool("RAPIDKIT_OBSERVABILITY_METRICS_PROCESS"),
        tracing_enabled=_parse_bool("RAPIDKIT_OBSERVABILITY_TRACING_ENABLED"),
        tracing_exporter=_get_env("RAPIDKIT_OBSERVABILITY_TRACING_EXPORTER"),
        tracing_endpoint=_get_env("RAPIDKIT_OBSERVABILITY_TRACING_ENDPOINT"),
        tracing_sample_ratio=_parse_float("RAPIDKIT_OBSERVABILITY_TRACING_SAMPLE_RATIO"),
        tracing_include_headers=_parse_bool("RAPIDKIT_OBSERVABILITY_TRACING_HEADERS"),
        logging_level=_get_env("RAPIDKIT_OBSERVABILITY_LOG_LEVEL"),
        logging_structured=_parse_bool("RAPIDKIT_OBSERVABILITY_STRUCTURED_LOGGING"),
        logging_include_trace_ids=_parse_bool("RAPIDKIT_OBSERVABILITY_INCLUDE_TRACE_IDS"),
        events_buffer_size=_parse_int("RAPIDKIT_OBSERVABILITY_EVENTS_BUFFER"),
        events_flush_interval=_parse_int("RAPIDKIT_OBSERVABILITY_EVENTS_FLUSH_INTERVAL"),
        events_audit_enabled=_parse_bool("RAPIDKIT_OBSERVABILITY_EVENTS_AUDIT"),
        retry_attempts=_parse_int("RAPIDKIT_OBSERVABILITY_RETRY_ATTEMPTS"),
    )


def _merge_nested(mapping: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(mapping, Mapping):
        return {}
    return {
        key: (dict(value) if isinstance(value, Mapping) else value)
        for key, value in mapping.items()
    }


def _mutate_defaults(
    defaults: Mapping[str, Any], state: ObservabilityOverrideState
) -> dict[str, Any]:
    mutated = _merge_nested(defaults)

    if state.service_name:
        mutated["service_name"] = state.service_name
    if state.environment:
        mutated["environment"] = state.environment

    resource_attributes = _merge_nested(mutated.get("resource_attributes", {}))
    if state.resource_attributes:
        resource_attributes.update(state.resource_attributes)
    mutated["resource_attributes"] = resource_attributes

    metrics = _merge_nested(mutated.get("metrics", {}))
    if state.metrics_enabled is not None:
        metrics["enabled"] = state.metrics_enabled
    if state.metrics_exporter:
        metrics["exporter"] = state.metrics_exporter
    if state.metrics_endpoint:
        metrics["endpoint"] = state.metrics_endpoint
    if state.metrics_namespace:
        metrics["namespace"] = state.metrics_namespace
    if state.metrics_labels:
        default_labels = _merge_nested(metrics.get("default_labels", {}))
        default_labels.update(state.metrics_labels)
        metrics["default_labels"] = default_labels
    if state.metrics_buckets is not None:
        metrics["buckets"] = list(state.metrics_buckets)
    if state.metrics_retention is not None:
        metrics["retention_seconds"] = max(state.metrics_retention, 0)
    if state.metrics_process_metrics is not None:
        metrics["register_process_metrics"] = state.metrics_process_metrics
    mutated["metrics"] = metrics

    tracing = _merge_nested(mutated.get("tracing", {}))
    if state.tracing_enabled is not None:
        tracing["enabled"] = state.tracing_enabled
    if state.tracing_exporter:
        tracing["exporter"] = state.tracing_exporter
    if state.tracing_endpoint:
        tracing["endpoint"] = state.tracing_endpoint
    if state.tracing_sample_ratio is not None:
        tracing["sample_ratio"] = max(0.0, min(state.tracing_sample_ratio, 1.0))
    if state.tracing_include_headers is not None:
        tracing["include_headers"] = state.tracing_include_headers
    mutated["tracing"] = tracing

    events = _merge_nested(mutated.get("events", {}))
    if state.events_buffer_size is not None:
        events["buffer_size"] = max(state.events_buffer_size, 0)
    if state.events_flush_interval is not None:
        events["flush_interval_seconds"] = max(state.events_flush_interval, 0)
    if state.events_audit_enabled is not None:
        events["audit_enabled"] = state.events_audit_enabled
    mutated["events"] = events

    if state.logging_level:
        mutated["log_level"] = state.logging_level
    if state.logging_structured is not None:
        mutated["structured_logging"] = state.logging_structured
    if state.logging_include_trace_ids is not None:
        mutated["include_trace_ids"] = state.logging_include_trace_ids
    if state.retry_attempts is not None:
        mutated["retry_attempts"] = max(state.retry_attempts, 0)

    return mutated


class ObservabilityCoreOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Observability Core."""

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
        # No post-processing hooks yet. Placeholder for future exporters.
        return None


__all__ = [
    "ObservabilityCoreOverrides",
    "ObservabilityOverrideState",
    "resolve_override_state",
    "DEFAULTS_KEY",
]
