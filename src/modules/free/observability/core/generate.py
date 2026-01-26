#!/usr/bin/env python3
"""Unified module generator for Observability Core."""

from __future__ import annotations

import sys
from pathlib import Path
from traceback import TracebackException
from typing import Any, Dict, Mapping, Optional

import yaml

from modules.shared.exceptions import ModuleGeneratorError
from modules.shared.generator import TemplateRenderer, format_missing_dependencies
from modules.shared.generator.module_generator import BaseModuleGenerator
from modules.shared.versioning import ensure_version_consistency

from .frameworks import get_plugin, list_available_plugins
from .overrides import DEFAULTS_KEY, ObservabilityCoreOverrides

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "observability_core"
MODULE_CLASS = "ObservabilityCore"
MODULE_TITLE = "Observability Core"
MODULE_TIER = "free"
MODULE_SLUG = "free/observability/observability_core"

PYTHON_RUNTIME_REL = "src/modules/free/observability/core/observability_core.py"
PYTHON_TYPES_REL = "src/modules/free/observability/core/types/observability_core.py"
PYTHON_HEALTH_REL = "src/health/observability_core.py"
FASTAPI_ROUTER_REL = "src/modules/free/observability/core/routers/observability_core.py"
FASTAPI_CONFIG_REL = "config/observability/observability_core.yaml"
FASTAPI_TEST_REL = "tests/modules/integration/observability/test_observability_core_integration.py"

NEST_SERVICE_REL = (
    "src/modules/free/observability/core/observability-core/observability-core.service.ts"
)
NEST_CONTROLLER_REL = (
    "src/modules/free/observability/core/observability-core/observability-core.controller.ts"
)
NEST_MODULE_REL = (
    "src/modules/free/observability/core/observability-core/observability-core.module.ts"
)
NEST_CONFIGURATION_REL = (
    "src/modules/free/observability/core/observability-core/observability-core.configuration.ts"
)
NEST_HEALTH_CONTROLLER_REL = "src/health/observability-core-health.controller.ts"
NEST_HEALTH_MODULE_REL = "src/health/observability-core-health.module.ts"
NEST_TEST_REL = "tests/modules/integration/observability/observability_core.integration.spec.ts"
VENDOR_CONFIGURATION_REL = "nestjs/configuration.js"

DEFAULT_METRICS_ENDPOINT = "/metrics"


class GeneratorError(ModuleGeneratorError):
    """Explicit generator failure carrying guidance for maintainers."""

    def __init__(
        self,
        message: str,
        *,
        exit_code: int = 1,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        error_context = context or {}
        error_context["exit_code"] = exit_code
        super().__init__(message, context=error_context)
        self.exit_code = exit_code


def _extract_defaults(config: Mapping[str, Any]) -> Dict[str, Any]:
    defaults = config.get("defaults")
    if isinstance(defaults, Mapping):
        return dict(defaults)
    return {}


class ObservabilityModuleGenerator(BaseModuleGenerator):
    """Generator orchestrating vendor runtime and framework variants."""

    def __init__(self, overrides: ObservabilityCoreOverrides | None = None) -> None:
        self._overrides = overrides
        super().__init__(
            module_root=MODULE_ROOT,
            templates_root=MODULE_ROOT,
            project_root=PROJECT_ROOT,
            module_identifier=MODULE_NAME,
            get_plugin=get_plugin,
            list_plugins=list_available_plugins,
            error_cls=GeneratorError,
        )
        if self._overrides is None:
            self._overrides = ObservabilityCoreOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> ObservabilityCoreOverrides:
        if self._overrides is None:
            raise RuntimeError("Observability overrides not initialised")
        return self._overrides

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        module_name = str(config.get("name", MODULE_NAME))
        version = config.get("version", "0.0.0")
        defaults = {
            "enabled": True,
            "service_name": "rapidkit-app",
            "environment": "local",
            "log_level": "INFO",
            "structured_logging": True,
            "include_trace_ids": True,
            "resource_attributes": {
                "deployment": "local",
                "owner": "platform",
            },
            "retry_attempts": 3,
            "metrics": {
                "enabled": True,
                "exporter": "prometheus",
                "endpoint": DEFAULT_METRICS_ENDPOINT,
                "namespace": "rapidkit",
                "default_labels": {
                    "service": "rapidkit-app",
                    "environment": "local",
                },
                "buckets": [0.1, 0.5, 1, 2.5, 5, 10],
                "retention_seconds": 600,
                "register_process_metrics": True,
            },
            "tracing": {
                "enabled": False,
                "exporter": "console",
                "endpoint": None,
                "sample_ratio": 0.25,
                "include_headers": True,
            },
            "events": {
                "buffer_size": 1000,
                "flush_interval_seconds": 5,
                "audit_enabled": False,
            },
            "dashboards": {
                "enabled": False,
                "emit_reference_links": True,
            },
        }
        defaults.update(_extract_defaults(config))

        metrics_section = defaults.get("metrics")
        metrics_cfg: Mapping[str, Any] = (
            metrics_section if isinstance(metrics_section, Mapping) else {}
        )
        metrics_endpoint = metrics_cfg.get("endpoint", DEFAULT_METRICS_ENDPOINT)

        metrics_defaults = dict(metrics_cfg)

        tracing_section = defaults.get("tracing")
        tracing_defaults = dict(tracing_section) if isinstance(tracing_section, Mapping) else {}
        logging_section = defaults.get("logging")
        logging_defaults = dict(logging_section) if isinstance(logging_section, Mapping) else {}
        events_section = defaults.get("events")
        events_defaults = dict(events_section) if isinstance(events_section, Mapping) else {}
        resource_section = defaults.get("resource_attributes")
        resource_attributes = (
            dict(resource_section) if isinstance(resource_section, Mapping) else {}
        )

        return {
            "module_name": module_name,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "module_tier": MODULE_TIER,
            "module_slug": MODULE_SLUG,
            "module_kebab": module_name.replace("_", "-"),
            "rapidkit_vendor_module": module_name,
            "rapidkit_vendor_version": version,
            "rapidkit_vendor_runtime_relative": PYTHON_RUNTIME_REL,
            "rapidkit_vendor_types_relative": PYTHON_TYPES_REL,
            "rapidkit_vendor_health_relative": PYTHON_HEALTH_REL,
            "rapidkit_vendor_fastapi_router_relative": FASTAPI_ROUTER_REL,
            "rapidkit_vendor_nest_service_relative": NEST_SERVICE_REL,
            "rapidkit_vendor_nest_controller_relative": NEST_CONTROLLER_REL,
            "rapidkit_vendor_nest_module_relative": NEST_MODULE_REL,
            "rapidkit_vendor_configuration_relative": VENDOR_CONFIGURATION_REL,
            "python_runtime_relative": PYTHON_RUNTIME_REL,
            "python_types_relative": PYTHON_TYPES_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "fastapi_router_relative": FASTAPI_ROUTER_REL,
            "fastapi_config_relative": FASTAPI_CONFIG_REL,
            "fastapi_test_relative": FASTAPI_TEST_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_controller_relative": NEST_CONTROLLER_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "nest_configuration_relative": NEST_CONFIGURATION_REL,
            "nest_health_controller_relative": NEST_HEALTH_CONTROLLER_REL,
            "nest_health_module_relative": NEST_HEALTH_MODULE_REL,
            "nest_test_relative": NEST_TEST_REL,
            DEFAULTS_KEY: defaults,
            "observability_defaults": defaults,
            "metrics_defaults": metrics_defaults,
            "tracing_defaults": tracing_defaults,
            "logging_defaults": logging_defaults,
            "events_defaults": events_defaults,
            "resource_attributes_defaults": resource_attributes,
            "retry_attempts_default": defaults.get("retry_attempts", 3),
            "enabled_by_default": defaults.get("enabled", True),
            "metrics_endpoint": metrics_endpoint,
            "metrics_exporter": metrics_cfg.get("exporter", "prometheus"),
        }

    def apply_base_context_overrides(self, context: Mapping[str, Any]) -> dict[str, Any]:
        return self.overrides.apply_base_context(context)

    def apply_variant_context_pre(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:
        return self.overrides.apply_variant_context_pre(context, variant_name=variant_name)

    def apply_variant_context_post(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:
        return self.overrides.apply_variant_context_post(context, variant_name=variant_name)

    def post_variant_generation(
        self,
        *,
        variant_name: str,
        target_dir: Path,
        enriched_context: Mapping[str, Any],
    ) -> None:
        self.overrides.post_variant_generation(
            variant_name=variant_name,
            target_dir=target_dir,
            enriched_context=enriched_context,
        )


def _create_generator(
    overrides: ObservabilityCoreOverrides | None = None,
) -> ObservabilityModuleGenerator:
    return ObservabilityModuleGenerator(overrides=overrides)


def load_module_config() -> Dict[str, Any]:
    return dict(_create_generator().load_module_config())


def build_base_context(config: Mapping[str, Any]) -> Dict[str, Any]:
    return dict(_create_generator().build_base_context(config))


def generate_vendor_files(
    config: Mapping[str, Any],
    target_dir: Path,
    renderer: TemplateRenderer,
    context: Mapping[str, Any],
) -> None:
    _create_generator().generate_vendor_files(config, target_dir, renderer, context)


def generate_variant_files(
    variant_name: str,
    target_dir: Path,
    renderer: TemplateRenderer,
    context: Mapping[str, Any],
    overrides: ObservabilityCoreOverrides | None = None,
) -> None:
    _create_generator(overrides=overrides).generate_variant_files(
        variant_name,
        target_dir,
        renderer,
        context,
    )


def main() -> None:
    expected_arg_count = 3
    if len(sys.argv) != expected_arg_count:
        available_plugins = list_available_plugins()
        available_names = ", ".join(sorted(available_plugins))
        guidance = (
            "Usage: python -m modules.free.observability.observability_core.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.observability.observability_core.generate fastapi ../../examples/observability-core\n"
            f"Available frameworks: {available_names or '<none registered>'}"
        )
        raise GeneratorError(
            guidance,
            context={
                "provided_args": sys.argv[1:],
                "expected_arg_count": expected_arg_count - 1,
            },
        )

    variant_name = sys.argv[1]
    target_dir = Path(sys.argv[2]).resolve()

    missing_optional_dependencies: Dict[str, str] = {}
    generator = ObservabilityModuleGenerator()

    try:
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        if version_updated:
            print(f"Auto bumped observability module version to {config['version']}")
        renderer = generator.create_renderer()

        generator.generate_vendor_files(config, target_dir, renderer, base_context)
        generator.generate_variant_files(variant_name, target_dir, renderer, base_context)
    except GeneratorError as exc:
        print(f"❌ Generator Error: {exc}")
        if exc.context:
            print("Context:")
            for key, value in exc.context.items():
                print(f"  {key}: {value}")
        dep_hint = format_missing_dependencies(missing_optional_dependencies)
        if dep_hint:
            print(f"\n{dep_hint}")
        sys.exit(exc.exit_code)
    except (RuntimeError, OSError, yaml.YAMLError) as exc:
        print("❌ Generator failed with an unexpected error:")
        traceback = "\n".join(TracebackException.from_exception(exc).format())
        print(traceback)
        print(
            "💡 If this persists, run 'rapidkit modules doctor observability_core' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
