#!/usr/bin/env python3
"""Unified module generator for Db Sqlite."""

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
from .overrides import DbSqliteOverrides

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "db_sqlite"
MODULE_CLASS = "DbSqlite"
MODULE_TITLE = "Db Sqlite"
MODULE_TIER = "free"
MODULE_CATEGORY = "database"
MODULE_CATEGORY_DISPLAY = "database"
MODULE_KEBAB = "db-sqlite"
MODULE_IMPORT_PATH = "modules.free.database.db_sqlite"
MODULE_BASE = "src/modules/free/database/db_sqlite"
PYTHON_OUTPUT_REL = f"{MODULE_BASE}/db_sqlite.py"
NEST_OUTPUT_REL = f"{MODULE_BASE}/db-sqlite/db-sqlite.service.ts"
FASTAPI_CONFIG_REL = "config/database/db_sqlite.yaml"
FASTAPI_TEST_REL = "tests/modules/integration/database/test_db_sqlite_integration.py"
NEST_CONFIGURATION_REL = f"{MODULE_BASE}/db-sqlite/db-sqlite.configuration.ts"
NEST_HEALTH_CONTROLLER_REL = f"{MODULE_BASE}/health/db-sqlite-health.controller.ts"
NEST_HEALTH_MODULE_REL = f"{MODULE_BASE}/health/db-sqlite-health.module.ts"
NEST_TEST_REL = "tests/modules/integration/database/db_sqlite.integration.spec.ts"
VENDOR_CONFIGURATION_REL = "nestjs/configuration.js"


class GeneratorError(ModuleGeneratorError):
    """Explicit generator failure carrying helpful metadata."""

    def __init__(
        self,
        message: str,
        *,
        exit_code: int = 1,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:  # pragma: no cover - exercised in CLI flows
        super().__init__(message, context=context or {})
        self.exit_code = exit_code


def _defaults_from_config(config: Mapping[str, Any]) -> Dict[str, Any]:
    defaults = config.get("defaults")
    if isinstance(defaults, Mapping):
        return dict(defaults)
    return {}  # pragma: no cover - benign fallback


def infer_vendor_settings_path(config: Mapping[str, Any]) -> str:
    vendor_cfg = config.get("generation", {}).get("vendor", {})
    for entry in vendor_cfg.get("files", []):
        template_name = entry.get("template", "")
        relative = entry.get("relative")
        if isinstance(relative, str) and template_name.endswith(f"{MODULE_NAME}.py.j2"):
            return relative
    return PYTHON_OUTPUT_REL  # pragma: no cover - default path used when config omits vendor file


class DbSqliteModuleGenerator(BaseModuleGenerator):
    """Module generator that embraces the shared plugin architecture."""

    def __init__(self, overrides: Optional[DbSqliteOverrides] = None) -> None:
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
            self._overrides = DbSqliteOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> DbSqliteOverrides:
        if self._overrides is None:
            raise RuntimeError(
                "Db Sqlite overrides not initialised"
            )  # pragma: no cover - defensive
        return self._overrides

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        defaults = _defaults_from_config(config)
        pool_defaults = {}
        if isinstance(defaults.get("pool"), Mapping):
            pool_defaults = dict(defaults["pool"])  # pragma: no cover - optional pool config
        pragma_defaults: Dict[str, str] = {}
        pragmas = defaults.get("pragmas")
        if isinstance(pragmas, Mapping):
            pragma_defaults = {
                str(key): str(value) for key, value in pragmas.items()
            }  # pragma: no cover - optional pragmas

        module = str(config.get("name", MODULE_NAME))
        version = str(config.get("version", "0.0.0"))
        enabled_default = bool(defaults.get("enabled", True))
        isolation_level = defaults.get("isolation_level")
        detect_types = defaults.get("detect_types")
        check_same_thread = bool(defaults.get("check_same_thread", False))
        retry_attempts = int(defaults.get("retry_attempts", 0))

        return {
            "rapidkit_vendor_module": module,
            "rapidkit_vendor_version": version,
            "rapidkit_vendor_relative_path": infer_vendor_settings_path(config),
            "rapidkit_vendor_configuration_relative": VENDOR_CONFIGURATION_REL,
            "module_name": module,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "python_output_relative": PYTHON_OUTPUT_REL,
            "nest_output_relative": NEST_OUTPUT_REL,
            "module_tier": MODULE_TIER,
            "module_kebab": MODULE_KEBAB,
            "module_category": MODULE_CATEGORY,
            "module_category_display": MODULE_CATEGORY_DISPLAY,
            "module_import_path": MODULE_IMPORT_PATH,
            "fastapi_config_relative": FASTAPI_CONFIG_REL,
            "fastapi_test_relative": FASTAPI_TEST_REL,
            "nest_configuration_relative": NEST_CONFIGURATION_REL,
            "nest_health_controller_relative": NEST_HEALTH_CONTROLLER_REL,
            "nest_health_module_relative": NEST_HEALTH_MODULE_REL,
            "nest_test_relative": NEST_TEST_REL,
            "enabled_by_default": enabled_default,
            "default_database_path": defaults.get(
                "database_path",
                "./.rapidkit/runtime/sqlite/app.db",
            ),
            "default_create_if_missing": bool(defaults.get("create_if_missing", True)),
            "default_timeout_seconds": float(defaults.get("timeout_seconds", 30.0)),
            "default_isolation_level": isolation_level,
            "default_detect_types": detect_types,
            "default_check_same_thread": check_same_thread,
            "default_retry_attempts": retry_attempts,
            "default_pragmas": pragma_defaults,
            "default_pool": {
                "max_size": int(pool_defaults.get("max_size", 4)),
                "recycle_seconds": int(pool_defaults.get("recycle_seconds", 600)),
            },
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


def _create_generator(overrides: Optional[DbSqliteOverrides] = None) -> DbSqliteModuleGenerator:
    return DbSqliteModuleGenerator(overrides=overrides)


def load_module_config() -> Dict[str, Any]:
    generator = _create_generator()
    config = generator.load_module_config()
    return dict(config)


def build_base_context(
    config: Mapping[str, Any],
) -> Dict[str, Any]:  # pragma: no cover - thin wrapper
    generator = _create_generator()
    return dict(generator.build_base_context(config))


def generate_vendor_files(
    config: Mapping[str, Any],
    target_dir: Path,
    renderer: TemplateRenderer,
    context: Mapping[str, Any],
    overrides: Optional[DbSqliteOverrides] = None,
) -> None:  # pragma: no cover - thin wrapper used in integration flows
    generator = _create_generator(overrides=overrides)
    generator.generate_vendor_files(config, target_dir, renderer, context)


def generate_variant_files(
    config: Mapping[str, Any],
    variant_name: str,
    target_dir: Path,
    renderer: TemplateRenderer,
    context: Mapping[str, Any],
    overrides: Optional[DbSqliteOverrides] = None,
) -> None:  # pragma: no cover - thin wrapper used in integration flows
    _ = config  # Preserve backwards-compatible signature
    generator = _create_generator(overrides=overrides)
    generator.generate_variant_files(variant_name, target_dir, renderer, context)


def main() -> None:  # pragma: no cover - CLI entrypoint exercised via E2E flows
    expected_arg_count = 3
    if len(sys.argv) != expected_arg_count:
        available_plugins = list_available_plugins()
        available_names = ", ".join(available_plugins.keys()) or "<none>"
        guidance = (
            "Usage: python -m modules.free.database.db_sqlite.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.database.db_sqlite.generate fastapi ../../examples/db_sqlite\n"
            f"Available frameworks: {available_names}"
        )
        raise GeneratorError(
            guidance,
            exit_code=2,
            context={"provided_args": sys.argv[1:], "available_frameworks": available_plugins},
        )

    variant_name = sys.argv[1]
    target_dir = Path(sys.argv[2]).resolve()

    generator = DbSqliteModuleGenerator()
    missing_optional_dependencies: Dict[str, str] = {}

    try:
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.build_base_context(config)
        enriched_context = generator.apply_base_context_overrides(base_context)
        if version_updated:
            print(f"Auto bumped db_sqlite module version to {config['version']}")
        renderer = generator.create_renderer()

        generator.generate_vendor_files(config, target_dir, renderer, enriched_context)
        generator.generate_variant_files(variant_name, target_dir, renderer, enriched_context)
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
            "💡 If this persists, run 'rapidkit modules doctor db_sqlite' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()


__all__ = [
    "DbSqliteModuleGenerator",
    "load_module_config",
    "build_base_context",
    "generate_vendor_files",
    "generate_variant_files",
    "main",
]
