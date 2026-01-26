#!/usr/bin/env python3
"""Unified module generator for Api Keys."""

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
from .overrides import ApiKeysOverrides

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "api_keys"
MODULE_CLASS = "ApiKeys"
MODULE_TITLE = "API Keys"
MODULE_TIER = "free"
MODULE_SLUG = "free/auth/api_keys"
# New module layout under src/modules/<tier>/<category>/<slug>
MODULE_BASE = "src/modules/free/auth/api_keys"

PYTHON_RUNTIME_REL = f"{MODULE_BASE}/api_keys.py"
PYTHON_TYPES_REL = f"{MODULE_BASE}/types/api_keys.py"
PYTHON_HEALTH_REL = "src/health/api_keys.py"
FASTAPI_ROUTER_REL = f"{MODULE_BASE}/routers/api_keys.py"

NEST_SERVICE_REL = f"{MODULE_BASE}/api-keys.service.ts"
NEST_CONTROLLER_REL = f"{MODULE_BASE}/api-keys.controller.ts"
NEST_MODULE_REL = f"{MODULE_BASE}/api-keys.module.ts"

DEFAULTS_KEY = "api_keys_defaults"


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


class ApiKeysModuleGenerator(BaseModuleGenerator):
    """Module generator orchestrating vendor runtime and framework variants for API keys."""

    def __init__(self, overrides: ApiKeysOverrides | None = None) -> None:
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
            self._overrides = ApiKeysOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> ApiKeysOverrides:
        if self._overrides is None:
            raise RuntimeError("ApiKeys overrides not initialised")
        return self._overrides

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        module_name = str(config.get("name", MODULE_NAME))
        version = config.get("version", "0.0.0")
        defaults = {
            "key_prefix": "rk",
            "display_prefix": "rk_live_",
            "token_separator": ".",
            "secret_bytes": 32,
            "prefix_bytes": 6,
            "prefix_charset": "ABCDEFGHJKLMNPQRSTUVWXYZ23456789",
            "hash_algorithm": "sha256",
            "pepper_env": "RAPIDKIT_API_KEYS_PEPPER",
            "default_scopes": ["read"],
            "allowed_scopes": ["read", "write", "admin"],
            "allow_scope_wildcards": False,
            "ttl_hours": None,
            "rotation_days": 90,
            "max_active_per_owner": 25,
            "leak_window_hours": 72,
            "persist_last_used": True,
            "audit_trail": True,
        }
        defaults.update(_extract_defaults(config))

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
            "python_runtime_relative": PYTHON_RUNTIME_REL,
            "python_types_relative": PYTHON_TYPES_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "fastapi_router_relative": FASTAPI_ROUTER_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_controller_relative": NEST_CONTROLLER_REL,
            "nest_module_relative": NEST_MODULE_REL,
            DEFAULTS_KEY: defaults,
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


def _create_generator(overrides: ApiKeysOverrides | None = None) -> ApiKeysModuleGenerator:
    return ApiKeysModuleGenerator(overrides=overrides)


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
    overrides: ApiKeysOverrides | None = None,
) -> None:
    _create_generator(overrides=overrides).generate_variant_files(
        variant_name, target_dir, renderer, context
    )


def main() -> None:
    expected_arg_count = 3
    if len(sys.argv) != expected_arg_count:
        available_plugins = list_available_plugins()
        available_names = ", ".join(sorted(available_plugins))
        guidance = (
            "Usage: python -m modules.free.auth.api_keys.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.auth.api_keys.generate fastapi ../../examples/api-keys\n"
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
    generator = ApiKeysModuleGenerator()

    try:
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        if version_updated:
            print(f"Auto bumped api-keys module version to {config['version']}")
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
            "💡 If this persists, run 'rapidkit modules doctor api_keys' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
