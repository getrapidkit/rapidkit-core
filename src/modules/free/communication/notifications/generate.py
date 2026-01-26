#!/usr/bin/env python3
"""Unified module generator for Notifications."""

from __future__ import annotations

import sys
from pathlib import Path
from traceback import TracebackException
from typing import Any, Dict, Mapping, Optional, cast

import yaml

from modules.shared.exceptions import SettingsGeneratorError
from modules.shared.generator import TemplateRenderer, format_missing_dependencies
from modules.shared.generator.module_generator import BaseModuleGenerator
from modules.shared.versioning import ensure_version_consistency

from .frameworks import get_plugin, list_available_plugins
from .overrides import NotificationsOverrides

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "notifications"
MODULE_CLASS = "Notifications"
MODULE_TITLE = "Notifications"
MODULE_TIER = "free"
MODULE_SLUG = "free/communication/notifications"
VENDOR_RUNTIME_REL = "runtime/communication/notifications.py"
VENDOR_TYPES_REL = "runtime/communication/notifications_types.py"
VENDOR_CONFIG_REL = "notifications/nestjs/configuration.js"
VENDOR_CONFIG_DEST_REL = "notifications/nestjs/configuration.js"

# New module layout under src/modules/<tier>/<category>/<slug>
MODULE_BASE = "src/modules/free/communication/notifications"

PYTHON_RUNTIME_REL = f"{MODULE_BASE}/core/notifications.py"
PYTHON_ROUTES_REL = f"{MODULE_BASE}/routers/notifications.py"
PYTHON_HEALTH_REL = f"{MODULE_BASE}/health/notifications.py"
PYTHON_CONFIG_REL = "config/communication/notifications.yaml"
PYTHON_TEST_REL = "tests/modules/free/integration/notifications/test_notifications_integration.py"

NEST_SERVICE_REL = f"{MODULE_BASE}/notifications.service.ts"
NEST_CONTROLLER_REL = f"{MODULE_BASE}/notifications.controller.ts"
NEST_MODULE_REL = f"{MODULE_BASE}/notifications.module.ts"
NEST_CONFIG_REL = f"{MODULE_BASE}/notifications.configuration.ts"
NEST_HEALTH_REL = f"{MODULE_BASE}/notifications.health.ts"
NEST_TEST_REL = "tests/modules/integration/communication/notifications.integration.spec.ts"


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
    files_cfg = vendor_cfg.get("files", [])
    for entry in files_cfg:
        if not isinstance(entry, Mapping):
            continue
        template_name = entry.get("template", "")
        relative = entry.get("relative")
        if (
            isinstance(relative, str)
            and isinstance(template_name, str)
            and template_name.endswith(suffix)
        ):
            return relative
    return suffix


def _deep_copy(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _deep_copy(sub) for key, sub in value.items()}
    if isinstance(value, list):
        return [_deep_copy(item) for item in value]
    return value


def _load_defaults(config: Mapping[str, Any]) -> Dict[str, Any]:
    defaults = config.get("defaults")
    if isinstance(defaults, Mapping):
        return cast(Dict[str, Any], _deep_copy(defaults))
    return {}


class NotificationsModuleGenerator(BaseModuleGenerator):
    def __init__(self, overrides: NotificationsOverrides | None = None) -> None:
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
            self._overrides = NotificationsOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> NotificationsOverrides:
        if self._overrides is None:
            raise RuntimeError("Notifications overrides not initialized")
        return self._overrides

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        module_name = str(config.get("name", MODULE_NAME))
        defaults = _load_defaults(config)

        project_name = str(defaults.get("project_name") or "RapidKit App").strip()
        if not project_name:
            project_name = "RapidKit App"
        defaults.setdefault("project_name", project_name)
        project_slug = project_name.lower().replace(" ", "-")

        runtime_relative = _infer_vendor_relative(config, VENDOR_RUNTIME_REL)
        types_relative = _infer_vendor_relative(config, VENDOR_TYPES_REL)
        vendor_config_relative = _infer_vendor_relative(config, VENDOR_CONFIG_REL)

        dest_vendor_config_relative = VENDOR_CONFIG_DEST_REL

        base_context = {
            "rapidkit_vendor_module": module_name,
            "rapidkit_vendor_version": config.get("version", "0.0.0"),
            "rapidkit_vendor_runtime_relative": runtime_relative,
            "rapidkit_vendor_types_relative": types_relative,
            "rapidkit_vendor_configuration_relative": dest_vendor_config_relative,
            "rapidkit_vendor_configuration_source_relative": vendor_config_relative,
            "vendor_runtime_relative": runtime_relative,
            "vendor_types_relative": types_relative,
            "vendor_configuration_relative": dest_vendor_config_relative,
            "vendor_configuration_source_relative": vendor_config_relative,
            "module_name": module_name,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "module_tier": MODULE_TIER,
            "module_slug": MODULE_SLUG,
            "project_name": project_name,
            "project_slug": project_slug,
            "python_runtime_relative": PYTHON_RUNTIME_REL,
            "python_routes_relative": PYTHON_ROUTES_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "python_config_relative": PYTHON_CONFIG_REL,
            "python_test_relative": PYTHON_TEST_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_controller_relative": NEST_CONTROLLER_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "nest_config_relative": NEST_CONFIG_REL,
            "nest_health_relative": NEST_HEALTH_REL,
            "nest_test_relative": NEST_TEST_REL,
            "notifications_defaults": defaults,
        }
        return self.apply_base_context_overrides(base_context)

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


def _create_generator(
    overrides: NotificationsOverrides | None = None,
) -> NotificationsModuleGenerator:
    return NotificationsModuleGenerator(overrides=overrides)


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
    overrides: NotificationsOverrides | None = None,
) -> None:
    _create_generator(overrides=overrides).generate_variant_files(
        variant_name, target_dir, renderer, context
    )


def main() -> None:
    EXPECTED_ARG_COUNT = 3
    if len(sys.argv) != EXPECTED_ARG_COUNT:
        available_plugins = list_available_plugins()
        available_names = list(available_plugins.keys())
        guidance = (
            "Usage: python -m modules.free.communication.notifications.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.communication.notifications.generate fastapi ../../examples/notifications\n"
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
    generator = NotificationsModuleGenerator()

    try:
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        if version_updated:
            print(f"Auto bumped notifications module version to {config['version']}")
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
            "💡 If this persists, run 'rapidkit modules doctor notifications' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
