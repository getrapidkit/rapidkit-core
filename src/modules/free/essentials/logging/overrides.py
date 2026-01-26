"""Override contracts for the logging module."""

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
class LoggingOverrideState:
    """Snapshot of environment-driven overrides for generation."""

    level: Optional[str] = None
    format: Optional[str] = None
    sinks: Optional[tuple[str, ...]] = None
    async_queue: Optional[bool] = None
    file_path: Optional[str] = None
    sampling_rate: Optional[float] = None
    enable_redaction: Optional[bool] = None
    otel_bridge_enabled: Optional[bool] = None
    metrics_bridge_enabled: Optional[bool] = None
    request_context_enabled: Optional[bool] = None
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


def _parse_sinks(value: Optional[str]) -> Optional[tuple[str, ...]]:
    if value is None:
        return None
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                sinks = tuple(str(item).strip() for item in parsed if str(item).strip())
                return sinks or None
        except json.JSONDecodeError:
            return None
    parts = [segment.strip() for segment in value.split(",") if segment.strip()]
    return tuple(parts) or None


def _parse_float(name: str) -> Optional[float]:
    raw = _get_env(name)
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def resolve_override_state(module_root: Path) -> LoggingOverrideState:
    sinks = _parse_sinks(_get_env("RAPIDKIT_LOGGING_FORCE_SINKS"))

    async_queue = _parse_bool("RAPIDKIT_LOGGING_FORCE_ASYNC_QUEUE")
    enable_redaction = _parse_bool("RAPIDKIT_LOGGING_FORCE_REDACTION")
    otel_bridge = _parse_bool("RAPIDKIT_LOGGING_FORCE_OTEL")
    metrics_bridge = _parse_bool("RAPIDKIT_LOGGING_FORCE_METRICS")

    request_context_enabled: Optional[bool] = None
    disable_request_context = _parse_bool("RAPIDKIT_LOGGING_DISABLE_REQUEST_CONTEXT")
    if disable_request_context is True:
        request_context_enabled = False
    enable_request_context = _parse_bool("RAPIDKIT_LOGGING_ENABLE_REQUEST_CONTEXT")
    if enable_request_context is True:
        request_context_enabled = True

    extra_snippet_env = _get_env("RAPIDKIT_LOGGING_EXTRA_SNIPPET")
    extra_snippet_source: Optional[Path] = None
    if extra_snippet_env:
        candidate = Path(extra_snippet_env)
        if not candidate.is_absolute():
            candidate = module_root / candidate
        extra_snippet_source = candidate

    extra_dest_env = _get_env("RAPIDKIT_LOGGING_EXTRA_SNIPPET_DEST")
    extra_dest: Optional[Path] = None
    if extra_dest_env:
        extra_dest = Path(extra_dest_env)

    extra_variants_env = _get_env("RAPIDKIT_LOGGING_EXTRA_SNIPPET_VARIANTS")
    extra_variants: Optional[tuple[str, ...]] = None
    if extra_variants_env:
        extra_variants = tuple(
            variant.strip() for variant in extra_variants_env.split(",") if variant.strip()
        )

    return LoggingOverrideState(
        level=_get_env("RAPIDKIT_LOGGING_FORCE_LEVEL"),
        format=_get_env("RAPIDKIT_LOGGING_FORCE_FORMAT"),
        sinks=sinks,
        async_queue=async_queue,
        file_path=_get_env("RAPIDKIT_LOGGING_FORCE_FILE_PATH"),
        sampling_rate=_parse_float("RAPIDKIT_LOGGING_FORCE_SAMPLING"),
        enable_redaction=enable_redaction,
        otel_bridge_enabled=otel_bridge,
        metrics_bridge_enabled=metrics_bridge,
        request_context_enabled=request_context_enabled,
        extra_snippet_source=extra_snippet_source,
        extra_snippet_destination=extra_dest,
        extra_snippet_variants=extra_variants,
    )


def _mutate_defaults(defaults: Mapping[str, Any], state: LoggingOverrideState) -> dict[str, Any]:
    mutated = dict(defaults)
    if state.level:
        mutated["level"] = state.level.upper()
    if state.format:
        mutated["format"] = state.format.lower()
    if state.sinks:
        mutated["sinks"] = [sink.lower() for sink in state.sinks]
    if state.async_queue is not None:
        mutated["async_queue"] = state.async_queue
    if state.file_path:
        mutated["file_path"] = state.file_path
    if state.sampling_rate is not None:
        mutated["sampling_rate"] = state.sampling_rate
    if state.enable_redaction is not None:
        mutated["enable_redaction"] = state.enable_redaction
    if state.otel_bridge_enabled is not None:
        mutated["otel_bridge_enabled"] = state.otel_bridge_enabled
    if state.metrics_bridge_enabled is not None:
        mutated["metrics_bridge_enabled"] = state.metrics_bridge_enabled
    return mutated


class LoggingOverrides(ConfigurableOverrideMixin):
    """Extend or customise generated behaviour for Logging."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        self.state = resolve_override_state(self.module_root)
        super().__init__()

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        mutated = dict(context)
        defaults = context.get("logging_defaults", {})
        mutated["logging_defaults"] = _mutate_defaults(defaults, self.state)
        if self.state.request_context_enabled is not None:
            mutated["logging_request_context_enabled"] = self.state.request_context_enabled
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
            raise FileNotFoundError(f"Logging override snippet '{source}' does not exist.")

        if self.state.extra_snippet_variants:
            if variant_name not in self.state.extra_snippet_variants:
                return

        destination = self.state.extra_snippet_destination or Path("extras") / source.name
        output_path = target_dir / destination
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, output_path)


__all__ = ["LoggingOverrides", "LoggingOverrideState", "resolve_override_state"]
