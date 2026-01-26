#!/usr/bin/env python3
"""Unified module generator for Redis caching."""

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
from .overrides import RedisOverrides

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "redis"
MODULE_CLASS = "Redis"
MODULE_TITLE = "Redis Cache"
MODULE_TIER = "free"
MODULE_SLUG = "free/cache/redis"

MODULE_BASE = "src/modules/free/cache/redis"

PYTHON_CLIENT_REL = f"{MODULE_BASE}/client.py"
PYTHON_PACKAGE_REL = f"{MODULE_BASE}/__init__.py"
PYTHON_FACADE_REL = f"{MODULE_BASE}/redis.py"
PYTHON_HEALTH_REL = "src/health/redis.py"
PYTHON_ROUTES_REL = f"{MODULE_BASE}/routers/redis.py"

NEST_CONFIGURATION_REL = f"{MODULE_BASE}/configuration.ts"
NEST_SERVICE_REL = f"{MODULE_BASE}/redis.service.ts"
NEST_MODULE_REL = f"{MODULE_BASE}/redis.module.ts"
NEST_INDEX_REL = f"{MODULE_BASE}/index.ts"
NEST_VALIDATION_REL = f"{MODULE_BASE}/redis.validation.ts"
NEST_HEALTH_REL = f"{MODULE_BASE}/redis.health.ts"
VENDOR_NEST_CONFIGURATION_REL = "nestjs/configuration.js"


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
    config_defaults = config.get("defaults")
    if isinstance(config_defaults, Mapping):
        return dict(config_defaults)
    return {}


class RedisModuleGenerator(BaseModuleGenerator):
    """Module generator that bridges vendor artefacts and framework variants."""

    def __init__(self, overrides: RedisOverrides | None = None) -> None:
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
            self._overrides = RedisOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> RedisOverrides:
        if self._overrides is None:
            raise RuntimeError("Redis overrides not initialised")
        return self._overrides

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        module = str(config.get("name", MODULE_NAME))
        defaults = {
            "url": "redis://localhost:6379/0",
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": "",
            "use_tls": False,
            "preconnect": False,
            "connect_retries": 3,
            "connect_backoff_base": 0.5,
            "cache_ttl": 3600,
        }
        defaults.update(_defaults_from_config(config))

        project_name = defaults.get("project_name") or "RapidKit App"
        if not isinstance(project_name, str) or not project_name.strip():
            project_name = "RapidKit App"
        project_name = project_name.strip()
        project_slug = project_name.lower().replace(" ", "-")

        base_module = defaults.get("base_module")
        if isinstance(base_module, str):
            trimmed = base_module.strip()
            trimmed = trimmed.rstrip("/")
            trimmed = trimmed.rstrip(".")
            base_module = trimmed.replace("/", ".").strip(".")
        if not base_module:
            base_module = "src"

        return {
            "rapidkit_vendor_module": module,
            "rapidkit_vendor_version": config.get("version", "0.0.0"),
            "module_name": module,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "module_kebab": module.replace("_", "-"),
            "module_tier": MODULE_TIER,
            "module_slug": MODULE_SLUG,
            "rapidkit_vendor_client_relative": PYTHON_CLIENT_REL,
            "rapidkit_vendor_package_relative": PYTHON_PACKAGE_REL,
            "rapidkit_vendor_health_relative": PYTHON_HEALTH_REL,
            "rapidkit_vendor_routes_relative": PYTHON_ROUTES_REL,
            "rapidkit_vendor_nest_configuration_relative": VENDOR_NEST_CONFIGURATION_REL,
            "rapidkit_vendor_nest_service_relative": NEST_SERVICE_REL,
            "rapidkit_vendor_nest_module_relative": NEST_MODULE_REL,
            "rapidkit_vendor_nest_index_relative": NEST_INDEX_REL,
            "rapidkit_vendor_nest_validation_relative": NEST_VALIDATION_REL,
            "rapidkit_vendor_nest_health_relative": NEST_HEALTH_REL,
            "python_client_relative": PYTHON_CLIENT_REL,
            "python_package_relative": PYTHON_PACKAGE_REL,
            "python_facade_relative": PYTHON_FACADE_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "python_routes_relative": PYTHON_ROUTES_REL,
            "nest_configuration_relative": NEST_CONFIGURATION_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "nest_index_relative": NEST_INDEX_REL,
            "nest_validation_relative": NEST_VALIDATION_REL,
            "nest_health_relative": NEST_HEALTH_REL,
            "redis_defaults": defaults,
            "base_module": base_module,
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


def _create_generator(overrides: RedisOverrides | None = None) -> RedisModuleGenerator:
    return RedisModuleGenerator(overrides=overrides)


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
    overrides: RedisOverrides | None = None,
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
            "Usage: python -m modules.free.cache.redis.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.cache.redis.generate fastapi ../../examples/redis\n"
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
    generator = RedisModuleGenerator()

    try:
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        if version_updated:
            print(f"Auto bumped redis module version to {config['version']}")
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
        print("💡 If this persists, run 'rapidkit modules doctor redis' or reinstall dependencies.")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
