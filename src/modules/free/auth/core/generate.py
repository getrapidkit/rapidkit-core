#!/usr/bin/env python3
"""Unified module generator for authentication core primitives."""

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
from .overrides import AuthCoreOverrides

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "auth_core"
MODULE_CLASS = "AuthCore"
MODULE_TITLE = "Authentication Core"
MODULE_TIER = "free"
MODULE_SLUG = "free/auth/core"

# New module layout under src/modules/<tier>/<category>/<slug>
MODULE_BASE = "src/modules/free/auth/core"

PYTHON_RUNTIME_REL = f"{MODULE_BASE}/auth/core.py"
PYTHON_DEPENDENCY_REL = f"{MODULE_BASE}/auth/dependencies.py"
PYTHON_HEALTH_REL = "src/health/auth_core.py"

NEST_SERVICE_REL = f"{MODULE_BASE}/auth-core.service.ts"
NEST_MODULE_REL = f"{MODULE_BASE}/auth-core.module.ts"
NEST_INDEX_REL = f"{MODULE_BASE}/core/index.ts"


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


class AuthCoreModuleGenerator(BaseModuleGenerator):
    """Module generator orchestrating vendor runtime and framework variants."""

    def __init__(self, overrides: AuthCoreOverrides | None = None) -> None:
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
            self._overrides = AuthCoreOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> AuthCoreOverrides:
        if self._overrides is None:
            raise RuntimeError("AuthCore overrides not initialised")
        return self._overrides

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        defaults = {
            "hash_name": "sha256",
            "iterations": 390_000,
            "salt_bytes": 32,
            "token_bytes": 32,
            "token_ttl_seconds": 1_800,
            "pepper_env": "RAPIDKIT_AUTH_CORE_PEPPER",
            "issuer": "RapidKit",
            "policy": {
                "min_length": 12,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_digits": True,
                "require_symbols": False,
            },
        }
        defaults.update(_defaults_from_config(config))

        module_name = str(config.get("name", MODULE_NAME))
        version = config.get("version", "0.0.0")

        return {
            "module_name": module_name,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "module_tier": MODULE_TIER,
            "module_slug": MODULE_SLUG,
            "rapidkit_vendor_module": module_name,
            "rapidkit_vendor_version": version,
            "python_runtime_relative": PYTHON_RUNTIME_REL,
            "python_dependency_relative": PYTHON_DEPENDENCY_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "nest_index_relative": NEST_INDEX_REL,
            "rapidkit_vendor_python_relative": PYTHON_RUNTIME_REL,
            "rapidkit_vendor_dependency_relative": PYTHON_DEPENDENCY_REL,
            "rapidkit_vendor_health_relative": PYTHON_HEALTH_REL,
            "rapidkit_vendor_nest_service_relative": NEST_SERVICE_REL,
            "rapidkit_vendor_nest_module_relative": NEST_MODULE_REL,
            "rapidkit_vendor_nest_index_relative": NEST_INDEX_REL,
            "auth_core_defaults": defaults,
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


def _create_generator(overrides: AuthCoreOverrides | None = None) -> AuthCoreModuleGenerator:
    return AuthCoreModuleGenerator(overrides=overrides)


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
    overrides: AuthCoreOverrides | None = None,
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
            "Usage: python -m modules.free.auth.core.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.auth.core.generate fastapi ../../examples/auth-core\n"
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
    generator = AuthCoreModuleGenerator()

    try:
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        if version_updated:
            print(f"Auto bumped auth-core module version to {config['version']}")
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
            "💡 If this persists, run 'rapidkit modules doctor auth_core' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
