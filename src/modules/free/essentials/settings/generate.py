#!/usr/bin/env python3
"""Unified module generator producing vendor snapshots and project variants."""

from __future__ import annotations

import sys
from pathlib import Path
from traceback import TracebackException
from typing import Any, Dict, Mapping, Optional

import yaml

from modules.free.essentials.settings.frameworks import get_plugin, list_available_plugins
from modules.shared.exceptions import SettingsGeneratorError
from modules.shared.generator import TemplateRenderer, format_missing_dependencies
from modules.shared.generator.module_generator import BaseModuleGenerator
from modules.shared.versioning import ensure_version_consistency

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "settings"
MODULE_CLASS = "Settings"
MODULE_TITLE = "Application Settings"
MODULE_TIER = "free"
MODULE_SLUG = "free/essentials/settings"

MODULE_BASE = "src/modules/free/essentials/settings"

VENDOR_SETTINGS_REL = f"{MODULE_BASE}/settings.py"
VENDOR_CUSTOM_SOURCES_REL = f"{MODULE_BASE}/custom_sources.py"
VENDOR_HOT_RELOAD_REL = f"{MODULE_BASE}/hot_reload.py"
VENDOR_HEALTH_REL = f"{MODULE_BASE}/health/settings.py"
VENDOR_TYPES_REL = f"{MODULE_BASE}/settings_types.py"
VENDOR_CONFIGURATION_REL = "nestjs/configuration.js"
VENDOR_HEALTH_TS_REL = "nestjs/settings.health.ts"

PYTHON_SETTINGS_REL = f"{MODULE_BASE}/settings.py"
PYTHON_CUSTOM_SOURCES_REL = f"{MODULE_BASE}/custom_sources.py"
PYTHON_HOT_RELOAD_REL = f"{MODULE_BASE}/hot_reload.py"
PYTHON_HEALTH_REL = "src/health/settings.py"
PYTHON_PROJECT_HEALTH_REL = "src/health/settings.py"
PYTHON_ROUTER_REL = f"{MODULE_BASE}/routers/settings.py"
PYTHON_TEST_REL = "tests/modules/free/essentials/settings/test_settings_integration.py"

NEST_CONFIG_REL = f"{MODULE_BASE}/configuration.ts"
NEST_SERVICE_REL = f"{MODULE_BASE}/settings.service.ts"
NEST_CONTROLLER_REL = f"{MODULE_BASE}/settings.controller.ts"
NEST_MODULE_REL = f"{MODULE_BASE}/settings.module.ts"
NEST_HEALTH_REL = "src/health/settings.health.ts"
NEST_METADATA_REL = f"{MODULE_BASE}/settings.metadata.ts"
NEST_TEST_REL = "tests/modules/integration/essentials/settings/settings.integration.spec.ts"


class GeneratorError(SettingsGeneratorError):
    """Explicit generator failure carrying guidance for the maintainers."""

    def __init__(
        self, message: str, *, exit_code: int = 1, context: Optional[Dict[str, Any]] = None
    ) -> None:
        error_context = context or {}
        error_context["exit_code"] = exit_code
        super().__init__(message, context=error_context)
        self.exit_code = exit_code


def _infer_vendor_relative(config: Mapping[str, Any], suffix: str = VENDOR_SETTINGS_REL) -> str:
    """Attempt to resolve vendor-relative paths based on configuration."""

    vendor_cfg = (
        config.get("generation", {}).get("vendor", {}) if isinstance(config, Mapping) else {}
    )
    files_cfg = vendor_cfg.get("files", []) if isinstance(vendor_cfg, Mapping) else []
    for entry in files_cfg:
        if not isinstance(entry, Mapping):
            continue
        template_name = entry.get("template")
        relative = entry.get("relative")
        if not isinstance(template_name, str) or not isinstance(relative, str):
            continue
        suffix_name = Path(suffix).name
        if Path(relative).name == suffix_name:
            return relative
        template_basename = Path(template_name).name
        if template_basename.endswith(f"{suffix_name}.j2") or template_basename == suffix_name:
            return relative
    return suffix


def infer_vendor_settings_path(config: Mapping[str, Any]) -> str:
    """Backwards-compatible alias for settings vendor path inference."""

    return _infer_vendor_relative(config, VENDOR_SETTINGS_REL)


def _coerce_list(value: Any, fallback: list[str]) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return list(fallback)
        return [candidate]
    return list(fallback)


class SettingsModuleGenerator(BaseModuleGenerator):
    def __init__(self) -> None:
        super().__init__(
            module_root=MODULE_ROOT,
            templates_root=MODULE_ROOT,
            project_root=PROJECT_ROOT,
            module_identifier=MODULE_NAME,
            get_plugin=get_plugin,
            list_plugins=list_available_plugins,
            error_cls=GeneratorError,
        )

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        module_name = str(config.get("name", MODULE_NAME))
        module_version = str(config.get("version", "0.0.0"))

        vendor_settings_relative = _infer_vendor_relative(config, VENDOR_SETTINGS_REL)
        vendor_custom_sources_relative = _infer_vendor_relative(config, VENDOR_CUSTOM_SOURCES_REL)
        vendor_hot_reload_relative = _infer_vendor_relative(config, VENDOR_HOT_RELOAD_REL)
        vendor_health_relative = _infer_vendor_relative(config, VENDOR_HEALTH_REL)
        vendor_types_relative = _infer_vendor_relative(config, VENDOR_TYPES_REL)
        vendor_configuration_relative = _infer_vendor_relative(config, VENDOR_CONFIGURATION_REL)
        vendor_health_ts_relative = _infer_vendor_relative(config, VENDOR_HEALTH_TS_REL)

        settings_defaults = {
            "ENV": "development",
            "DEBUG": False,
            "PROJECT_NAME": "RapidKit App",
            "SECRET_KEY": "rapidkit-default-generated-secret",
            "VERSION": module_version or "1.0.0",
            "ALLOWED_HOSTS": ["*"],
            "CONFIG_FILES": [".env", ".env.local", "config.yaml"],
            "CONFIG_REFRESH_INTERVAL": 60,
            "VAULT_URL": "http://localhost:8200",
            "AWS_REGION": "us-east-1",
            "HOT_RELOAD_ENABLED": True,
            "HOT_RELOAD_ENV_ALLOWLIST": ["development", "staging"],
        }

        project_name = settings_defaults.get("PROJECT_NAME", "RapidKit App")
        project_slug = str(project_name).lower().replace(" ", "-")

        return {
            "rapidkit_vendor_module": module_name,
            "rapidkit_vendor_version": module_version,
            "rapidkit_vendor_relative_path": vendor_settings_relative,
            "rapidkit_vendor_settings_relative": vendor_settings_relative,
            "rapidkit_vendor_custom_sources_relative": vendor_custom_sources_relative,
            "rapidkit_vendor_hot_reload_relative": vendor_hot_reload_relative,
            "rapidkit_vendor_health_relative": vendor_health_relative,
            "rapidkit_vendor_types_relative": vendor_types_relative,
            "rapidkit_vendor_configuration_relative": vendor_configuration_relative,
            "rapidkit_vendor_health_ts_relative": vendor_health_ts_relative,
            "module_name": module_name,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "module_tier": MODULE_TIER,
            "module_slug": MODULE_SLUG,
            "python_settings_relative": PYTHON_SETTINGS_REL,
            "python_custom_sources_relative": PYTHON_CUSTOM_SOURCES_REL,
            "python_hot_reload_relative": PYTHON_HOT_RELOAD_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "python_project_health_relative": PYTHON_PROJECT_HEALTH_REL,
            "python_router_relative": PYTHON_ROUTER_REL,
            "python_test_relative": PYTHON_TEST_REL,
            "nest_config_relative": NEST_CONFIG_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_controller_relative": NEST_CONTROLLER_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "nest_health_relative": NEST_HEALTH_REL,
            "nest_metadata_relative": NEST_METADATA_REL,
            "nest_test_relative": NEST_TEST_REL,
            "settings_defaults": {
                **settings_defaults,
                "ALLOWED_HOSTS": _coerce_list(settings_defaults.get("ALLOWED_HOSTS"), ["*"]),
                "CONFIG_FILES": _coerce_list(settings_defaults.get("CONFIG_FILES"), [".env"]),
                "HOT_RELOAD_ENV_ALLOWLIST": _coerce_list(
                    settings_defaults.get("HOT_RELOAD_ENV_ALLOWLIST"), ["development"]
                ),
            },
            "enabled_features": ["extendable_settings", "rate-limiting", "users_profiles"],
            "project_name": project_name,
            "project_slug": project_slug,
        }


def _create_generator() -> SettingsModuleGenerator:
    return SettingsModuleGenerator()


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
) -> None:
    _create_generator().generate_variant_files(variant_name, target_dir, renderer, context)


def main() -> None:
    EXPECTED_ARG_COUNT = 3
    if len(sys.argv) != EXPECTED_ARG_COUNT:
        available_plugins = list_available_plugins()
        available_names = list(available_plugins.keys())
        guidance = (
            "Usage: python generate.py <framework> <target_dir>\n"
            f"Example: python generate.py fastapi ../../examples/fastapi\n"
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

    try:
        generator = SettingsModuleGenerator()
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.build_base_context(config)
        if version_updated:
            print(f"Auto bumped settings module version to {config['version']}")
        renderer = TemplateRenderer(MODULE_ROOT)

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
            "💡 If this persists, run 'rapidkit modules doctor settings' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
