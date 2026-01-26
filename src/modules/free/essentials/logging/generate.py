#!/usr/bin/env python3
"""Unified module generator for Logging."""

from __future__ import annotations

import sys
from pathlib import Path
from traceback import TracebackException
from typing import Any, Dict, Mapping, Optional

import yaml

from modules.shared.exceptions import SettingsGeneratorError
from modules.shared.generator import TemplateRenderer, format_missing_dependencies
from modules.shared.generator.module_generator import BaseModuleGenerator
from modules.shared.versioning import ensure_version_consistency

from .frameworks import get_plugin, list_available_plugins
from .overrides import LoggingOverrides

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "logging"
MODULE_CLASS = "Logging"
MODULE_TITLE = "Logging"
MODULE_TIER = "free"
MODULE_SLUG = "free/essentials/logging"

MODULE_BASE = "src/modules/free/essentials/logging"

VENDOR_RUNTIME_REL = f"{MODULE_BASE}/logging.py"
VENDOR_TYPES_REL = f"{MODULE_BASE}/logging_types.py"
VENDOR_CONFIG_REL = "nestjs/configuration.js"

PYTHON_RUNTIME_REL = f"{MODULE_BASE}/logging.py"
PYTHON_ROUTES_REL = f"{MODULE_BASE}/routers/logging.py"
PYTHON_HEALTH_REL = f"{MODULE_BASE}/health/logging.py"
PYTHON_CONFIG_REL = "src/modules/free/essentials/logging/config/logging.yaml"
PYTHON_TEST_REL = "tests/modules/free/essentials/logging/test_logging_integration.py"

NEST_SERVICE_REL = f"{MODULE_BASE}/logging.service.ts"
NEST_CONTROLLER_REL = f"{MODULE_BASE}/logging.controller.ts"
NEST_MODULE_REL = f"{MODULE_BASE}/logging.module.ts"
NEST_CONFIG_REL = f"{MODULE_BASE}/configuration.ts"
NEST_HEALTH_REL = f"{MODULE_BASE}/logging.health.ts"
NEST_TEST_REL = "tests/modules/integration/essentials/logging/logging.integration.spec.ts"


class GeneratorError(SettingsGeneratorError):
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


def _infer_vendor_relative(config: Mapping[str, Any], suffix: str) -> str:
    vendor_cfg = config.get("generation", {}).get("vendor", {})
    for entry in vendor_cfg.get("files", []):
        template_name = entry.get("template", "")
        relative = entry.get("relative")
        if not isinstance(relative, str) or not isinstance(template_name, str):
            continue
        suffix_name = Path(suffix).name
        if Path(relative).name == suffix_name:
            return relative
        template_basename = Path(template_name).name
        if template_basename.endswith(f"{suffix_name}.j2") or template_basename == suffix_name:
            return relative
    return suffix


class LoggingModuleGenerator(BaseModuleGenerator):
    def __init__(self, overrides: LoggingOverrides | None = None) -> None:
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
            self._overrides = LoggingOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> LoggingOverrides:
        if self._overrides is None:
            raise RuntimeError("Logging overrides not initialized")
        return self._overrides

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        module = str(config.get("name", MODULE_NAME))
        project_defaults = config.get("defaults", {}) if isinstance(config, Mapping) else {}
        project_name = str(project_defaults.get("project_name") or "RapidKit App").strip()
        if not project_name:
            project_name = "RapidKit App"
        project_slug = project_name.lower().replace(" ", "-")
        logging_defaults = {
            "level": "INFO",
            "format": "json",
            "sinks": ["stderr"],
            "async_queue": True,
            "file_path": "logs/app.log",
            "sampling_rate": 1.0,
            "enable_redaction": True,
            "otel_bridge_enabled": False,
            "metrics_bridge_enabled": False,
        }
        runtime_relative = _infer_vendor_relative(config, VENDOR_RUNTIME_REL)
        types_relative = _infer_vendor_relative(config, VENDOR_TYPES_REL)
        vendor_config_relative = _infer_vendor_relative(config, VENDOR_CONFIG_REL)

        return {
            "rapidkit_vendor_module": module,
            "rapidkit_vendor_version": config.get("version", "0.0.0"),
            "rapidkit_vendor_runtime_relative": runtime_relative,
            "rapidkit_vendor_types_relative": types_relative,
            "rapidkit_vendor_configuration_relative": vendor_config_relative,
            "rapidkit_vendor_relative_path": runtime_relative,
            "vendor_runtime_relative": runtime_relative,
            "vendor_types_relative": types_relative,
            "vendor_configuration_relative": vendor_config_relative,
            "module_name": module,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "module_tier": MODULE_TIER,
            "module_slug": MODULE_SLUG,
            "python_output_relative": PYTHON_RUNTIME_REL,
            "python_runtime_relative": PYTHON_RUNTIME_REL,
            "python_routes_relative": PYTHON_ROUTES_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "python_config_relative": PYTHON_CONFIG_REL,
            "python_test_relative": PYTHON_TEST_REL,
            "nest_output_relative": NEST_SERVICE_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_controller_relative": NEST_CONTROLLER_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "nest_config_relative": NEST_CONFIG_REL,
            "nest_health_relative": NEST_HEALTH_REL,
            "nest_test_relative": NEST_TEST_REL,
            "logging_defaults": logging_defaults,
            "logging_request_context_enabled": True,
            "project_name": project_name,
            "project_slug": project_slug,
        }

    def apply_base_context_overrides(self, context: Mapping[str, Any]) -> dict[str, Any]:
        return self.overrides.apply_base_context(context)

    def apply_variant_context_pre(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:
        return self.overrides.apply_variant_context_pre(context, variant_name=variant_name)

    def apply_variant_context_post(
        self, context: Mapping[str, Any], *, variant_name: str
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
    overrides: LoggingOverrides | None = None,
) -> LoggingModuleGenerator:
    return LoggingModuleGenerator(overrides=overrides)


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
    overrides: LoggingOverrides | None = None,
) -> None:
    _create_generator(overrides=overrides).generate_variant_files(
        variant_name, target_dir, renderer, context
    )


def main() -> None:
    expected_arg_count = 3
    if len(sys.argv) != expected_arg_count:
        available_plugins = list_available_plugins()
        available_names = list(available_plugins.keys())
        guidance = (
            "Usage: python -m modules.free.essentials.logging.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.essentials.logging.generate fastapi ../../examples/logging\n"
            f"Available frameworks: {', '.join(available_names)}"
        )
        raise GeneratorError(
            guidance,
            exit_code=2,
            context={
                "provided_args": sys.argv[1:],
                "expected_arg_count": expected_arg_count - 1,
            },
        )

    variant_name = sys.argv[1]
    target_dir = Path(sys.argv[2]).resolve()

    missing_optional_dependencies: Dict[str, str] = {}
    generator = LoggingModuleGenerator()

    try:
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        if version_updated:
            print(f"Auto bumped module version to {config['version']}")
        renderer = generator.create_renderer()

        generator.generate_vendor_files(config, target_dir, renderer, base_context)
        generator.generate_variant_files(variant_name, target_dir, renderer, base_context)
    except GeneratorError as exc:
        print(f"❌ Generator Error: {exc.message}")
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
            "💡 If this persists, run 'rapidkit modules doctor logging' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
