#!/usr/bin/env python3
"""Unified module generator for Users Core."""

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
from .overrides import UsersCoreOverrides

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "users_core"
MODULE_CLASS = "UsersCore"
MODULE_TITLE = "Users Core"
MODULE_TIER = "free"
MODULE_SLUG = "free/users/users_core"
# New module layout under src/modules/<tier>/<category>/<slug>
MODULE_BASE = "src/modules/free/users/users_core"

VENDOR_RUNTIME_REL = f"{MODULE_BASE}/users_core.py"
VENDOR_HEALTH_REL = f"{MODULE_BASE}/health/users_core.py"
VENDOR_TYPES_REL = f"{MODULE_BASE}/users_core_types.py"
VENDOR_CONFIGURATION_REL = "nestjs/configuration.js"

PYTHON_SERVICE_REL = f"{MODULE_BASE}/core/users/service.py"
PYTHON_DEPENDENCIES_REL = f"{MODULE_BASE}/core/users/dependencies.py"
PYTHON_ROUTER_REL = f"{MODULE_BASE}/core/users/router.py"
PYTHON_SETTINGS_REL = f"{MODULE_BASE}/core/users/settings.py"
PYTHON_HEALTH_REL = f"{MODULE_BASE}/health/users_core.py"
PYTHON_RUNTIME_BRIDGE_REL = f"{MODULE_BASE}/users_core.py"
PYTHON_HEALTH_BRIDGE_REL = f"{MODULE_BASE}/health/users_core.py"
PYTHON_TYPES_BRIDGE_REL = f"{MODULE_BASE}/users_core_types.py"
FASTAPI_CONFIG_REL = f"{MODULE_BASE}/config/users_core.yaml"
FASTAPI_TEST_REL = "tests/modules/free/users/users_core/test_users_core_integration.py"

NEST_SERVICE_REL = f"{MODULE_BASE}/users-core.service.ts"
NEST_MODULE_REL = f"{MODULE_BASE}/users-core.module.ts"
NEST_INDEX_REL = f"{MODULE_BASE}/index.ts"
NEST_CONFIGURATION_REL = f"{MODULE_BASE}/users-core.configuration.ts"
NEST_HEALTH_CONTROLLER_REL = f"{MODULE_BASE}/health/users-core-health.controller.ts"
NEST_HEALTH_MODULE_REL = f"{MODULE_BASE}/health/users-core-health.module.ts"
NEST_TEST_REL = "tests/modules/free/users/users_core/users-core.integration.spec.ts"


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


def _defaults_from_config(config: Mapping[str, Any]) -> Dict[str, Any]:
    defaults = config.get("defaults")
    if isinstance(defaults, Mapping):
        return dict(defaults)
    return {}


class UsersCoreModuleGenerator(BaseModuleGenerator):
    """Module generator orchestrating vendor runtime and framework variants."""

    def __init__(self, overrides: UsersCoreOverrides | None = None) -> None:
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
            self._overrides = UsersCoreOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> UsersCoreOverrides:
        if self._overrides is None:
            raise RuntimeError("UsersCore overrides not initialised")
        return self._overrides

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        defaults = {
            "allow_registration": True,
            "enforce_unique_email": True,
            "default_locale": "en",
            "audit_log_enabled": True,
            "max_results_per_page": 100,
            "passwordless_supported": False,
            "supported_locales": ["en"],
        }
        defaults.update(_defaults_from_config(config))

        module_name = str(config.get("name", MODULE_NAME))
        version = config.get("version", "0.0.0")

        return {
            "module_name": module_name,
            "module_kebab": module_name.replace("_", "-"),
            "module_title": MODULE_TITLE,
            "module_class_name": MODULE_CLASS,
            "module_slug": MODULE_SLUG,
            "module_tier": MODULE_TIER,
            "rapidkit_vendor_module": module_name,
            "rapidkit_vendor_version": version,
            "rapidkit_vendor_relative_path": VENDOR_RUNTIME_REL,
            "rapidkit_vendor_health_relative": VENDOR_HEALTH_REL,
            "rapidkit_vendor_types_relative": VENDOR_TYPES_REL,
            "rapidkit_vendor_configuration_relative": VENDOR_CONFIGURATION_REL,
            "python_service_relative": PYTHON_SERVICE_REL,
            "python_dependencies_relative": PYTHON_DEPENDENCIES_REL,
            "python_router_relative": PYTHON_ROUTER_REL,
            "python_settings_relative": PYTHON_SETTINGS_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "python_runtime_bridge_relative": PYTHON_RUNTIME_BRIDGE_REL,
            "python_health_bridge_relative": PYTHON_HEALTH_BRIDGE_REL,
            "python_types_bridge_relative": PYTHON_TYPES_BRIDGE_REL,
            "fastapi_config_relative": FASTAPI_CONFIG_REL,
            "fastapi_test_relative": FASTAPI_TEST_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "nest_index_relative": NEST_INDEX_REL,
            "nest_configuration_relative": NEST_CONFIGURATION_REL,
            "nest_health_controller_relative": NEST_HEALTH_CONTROLLER_REL,
            "nest_health_module_relative": NEST_HEALTH_MODULE_REL,
            "nest_test_relative": NEST_TEST_REL,
            "users_core_defaults": defaults,
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
        enriched = dict(context)
        enriched.setdefault("module_name", context.get("module_name", MODULE_NAME))
        return self.overrides.apply_variant_context_post(enriched, variant_name=variant_name)

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


def _create_generator(overrides: UsersCoreOverrides | None = None) -> UsersCoreModuleGenerator:
    return UsersCoreModuleGenerator(overrides=overrides)


def load_module_config() -> Dict[str, Any]:
    return dict(_create_generator().load_module_config())


def build_base_context(config: Mapping[str, Any]) -> Dict[str, Any]:
    generator = _create_generator()
    context = generator.build_base_context(config)
    return generator.apply_base_context_overrides(context)


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
    overrides: UsersCoreOverrides | None = None,
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
            "Usage: python -m modules.free.users.users_core.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.users.users_core.generate fastapi ../../examples/users-core\n"
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

    try:
        generator = _create_generator()
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(
            config,
            module_root=MODULE_ROOT,
        )
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        if version_updated:
            print(f"Auto bumped users-core module version to {config['version']}")
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
        sys.exit(getattr(exc, "exit_code", 1))
    except (RuntimeError, OSError, yaml.YAMLError) as exc:
        print("❌ Generator failed with an unexpected error:")
        traceback = "\n".join(TracebackException.from_exception(exc).format())
        print(traceback)
        print(
            "💡 If this persists, run 'rapidkit modules doctor users_core' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
