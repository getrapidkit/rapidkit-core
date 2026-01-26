#!/usr/bin/env python3
"""Unified module generator for Middleware."""

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
from .overrides import MiddlewareOverrides

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "middleware"
MODULE_CLASS = "Middleware"
MODULE_TITLE = "Middleware"
MODULE_TIER = "free"
MODULE_SLUG = "free/essentials/middleware"
MODULE_BASE = "src/modules/free/essentials/middleware"
VENDOR_RUNTIME_REL = "middleware/fastapi/middleware.py"
VENDOR_TYPES_REL = "middleware/fastapi/types.py"
VENDOR_CONFIG_REL = "middleware/nestjs/configuration.js"

PYTHON_RUNTIME_REL = f"{MODULE_BASE}/middleware.py"
PYTHON_HEALTH_REL = f"{MODULE_BASE}/health/middleware.py"
PYTHON_PROJECT_HEALTH_REL = f"{MODULE_BASE}/health/middleware.py"
PYTHON_ROUTER_REL = f"{MODULE_BASE}/routers/middleware.py"
PYTHON_CONFIG_REL = "src/modules/free/essentials/middleware/config/middleware.yaml"
PYTHON_TEST_REL = "tests/modules/free/essentials/middleware/test_middleware_integration.py"

NEST_SERVICE_REL = f"{MODULE_BASE}/service.ts"
NEST_CONTROLLER_REL = f"{MODULE_BASE}/controller.ts"
NEST_MODULE_REL = f"{MODULE_BASE}/module.ts"
NEST_CONFIG_REL = f"{MODULE_BASE}/configuration.ts"
NEST_HEALTH_REL = f"{MODULE_BASE}/middleware.health.ts"
NEST_TEST_REL = "tests/modules/integration/essentials/middleware/middleware.integration.spec.ts"


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
    """Attempt to match a vendor relative path based on the configured files."""

    vendor_cfg = (
        config.get("generation", {}).get("vendor", {}) if isinstance(config, Mapping) else {}
    )
    for entry in vendor_cfg.get("files", []):
        template_name = entry.get("template") if isinstance(entry, Mapping) else None
        relative = entry.get("relative") if isinstance(entry, Mapping) else None
        if not isinstance(template_name, str) or not isinstance(relative, str):
            continue
        suffix_name = Path(suffix).name
        if Path(relative).name == suffix_name:
            return relative
        template_basename = Path(template_name).name
        if template_basename.endswith(f"{suffix_name}.j2") or template_basename == suffix_name:
            return relative
    return suffix


def _coerce_list(value: Any, fallback: list[str]) -> list[str]:
    """Return a list from arbitrary inputs, preserving fallback when invalid."""

    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return list(fallback)


class MiddlewareModuleGenerator(BaseModuleGenerator):
    def __init__(self, overrides: MiddlewareOverrides | None = None) -> None:
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
            self._overrides = MiddlewareOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> MiddlewareOverrides:
        if self._overrides is None:
            raise RuntimeError("Middleware overrides not initialized")
        return self._overrides

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        module = str(config.get("name", MODULE_NAME))
        project_defaults = config.get("defaults", {}) if isinstance(config, Mapping) else {}
        project_name = str(project_defaults.get("project_name") or "RapidKit App").strip()
        if not project_name:
            project_name = "RapidKit App"
        project_slug = project_name.lower().replace(" ", "-")
        defaults_mapping = config.get("defaults") if isinstance(config, Mapping) else {}
        defaults = defaults_mapping if isinstance(defaults_mapping, Mapping) else {}
        metadata_value = (
            defaults.get("metadata") if isinstance(defaults.get("metadata"), Mapping) else {}
        )
        service_name_value = defaults.get("service_name")
        if isinstance(service_name_value, str):
            service_name_value = service_name_value.strip() or None
        elif service_name_value is not None:
            service_name_value = str(service_name_value)

        middleware_defaults = {
            "enabled": bool(defaults.get("enabled", True)),
            "cors_enabled": bool(defaults.get("cors_enabled", False)),
            "cors_allow_origins": _coerce_list(defaults.get("cors_allow_origins"), ["*"]),
            "cors_allow_methods": _coerce_list(defaults.get("cors_allow_methods"), ["*"]),
            "cors_allow_headers": _coerce_list(defaults.get("cors_allow_headers"), ["*"]),
            "cors_allow_credentials": bool(defaults.get("cors_allow_credentials", True)),
            "process_time_header": bool(defaults.get("process_time_header", True)),
            "service_header": bool(defaults.get("service_header", True)),
            "service_header_name": str(defaults.get("service_header_name") or "X-Service"),
            "service_name": service_name_value,
            "custom_headers": bool(defaults.get("custom_headers", True)),
            "custom_header_name": str(defaults.get("custom_header_name") or "X-Custom-Header"),
            "custom_header_value": str(defaults.get("custom_header_value") or "RapidKit"),
            "metadata": dict(metadata_value) if isinstance(metadata_value, Mapping) else {},
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
            "python_health_relative": PYTHON_HEALTH_REL,
            "python_project_health_relative": PYTHON_PROJECT_HEALTH_REL,
            "python_router_relative": PYTHON_ROUTER_REL,
            "python_config_relative": PYTHON_CONFIG_REL,
            "python_test_relative": PYTHON_TEST_REL,
            "nest_output_relative": NEST_SERVICE_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_controller_relative": NEST_CONTROLLER_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "nest_config_relative": NEST_CONFIG_REL,
            "nest_health_relative": NEST_HEALTH_REL,
            "nest_test_relative": NEST_TEST_REL,
            "middleware_defaults": middleware_defaults,
            "project_name": project_name,
            "project_slug": project_slug,
        }

    def apply_base_context_overrides(self, context: Mapping[str, Any]) -> dict[str, Any]:
        return self.overrides.apply_base_context(context)

    def apply_variant_context_pre(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:
        return self.overrides.apply_variant_context(context)

    def apply_variant_context_post(
        self, context: Mapping[str, Any], *, variant_name: str
    ) -> dict[str, Any]:
        return self.overrides.apply_variant_context(context)


def _create_generator(overrides: MiddlewareOverrides | None = None) -> MiddlewareModuleGenerator:
    return MiddlewareModuleGenerator(overrides=overrides)


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
    overrides: MiddlewareOverrides | None = None,
) -> None:
    _create_generator(overrides=overrides).generate_variant_files(
        variant_name, target_dir, renderer, context
    )


def main() -> None:  # pragma: no cover - exercised via CLI integration tests
    EXPECTED_ARG_COUNT = 3
    if len(sys.argv) != EXPECTED_ARG_COUNT:
        available_plugins = list_available_plugins()
        available_names = list(available_plugins.keys())
        guidance = (
            "Usage: python -m modules.free.essentials.middleware.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.essentials.middleware.generate fastapi ../../examples/middleware\n"
            f"Available frameworks: {', '.join(available_names)}"
        )
        raise GeneratorError(
            guidance,
            exit_code=2,
            context={"provided_args": sys.argv[1:], "expected_arg_count": EXPECTED_ARG_COUNT - 1},
        )

    variant_name = sys.argv[1]
    target_dir = Path(sys.argv[2]).resolve()

    missing_optional_dependencies: Dict[str, str] = {}
    generator = MiddlewareModuleGenerator()

    try:
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        if version_updated:
            print(f"Auto bumped middleware module version to {config['version']}")
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
            "💡 If this persists, run 'rapidkit modules doctor middleware' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
