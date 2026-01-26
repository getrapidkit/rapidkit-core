#!/usr/bin/env python3
"""Unified module generator for PostgreSQL Database (db_postgres)."""

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

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "db_postgres"
MODULE_CLASS = "DatabasePostgres"
MODULE_TITLE = "PostgreSQL Database"
MODULE_TIER = "free"
MODULE_SLUG = "free/database/db_postgres"
VENDOR_DATABASE_REL = "src/modules/free/database/db_postgres/postgres.py"
VENDOR_HEALTH_REL = "src/health/postgres.py"
VENDOR_CONFIGURATION_REL = "nestjs/configuration.js"

PYTHON_DATABASE_REL = "src/modules/free/database/db_postgres/postgres.py"
PYTHON_HEALTH_REL = "src/health/postgres.py"
PYTHON_CONFIG_REL = "config/database/postgres.yaml"
PYTHON_TEST_REL = "tests/modules/integration/database/test_postgres_integration.py"

NEST_SERVICE_REL = "src/modules/free/database/db_postgres/postgres.service.ts"
NEST_MODULE_REL = "src/modules/free/database/db_postgres/postgres.module.ts"
NEST_HEALTH_CONTROLLER_REL = "src/health/postgres-health.controller.ts"
NEST_HEALTH_MODULE_REL = "src/health/postgres-health.module.ts"
NEST_CONFIG_REL = "nestjs/configuration.js"
NEST_TEST_REL = "tests/modules/integration/database/postgres.integration.spec.ts"

DATABASE_DEFAULTS: Dict[str, Any] = {
    "enabled": True,
    "database_url": "postgresql://postgres:postgres@localhost:5432/rapidkit",
    "test_database_url": "postgresql://postgres:postgres@localhost:5433/rapidkit_test",
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "echo": False,
    "expire_on_commit": False,
    "schema": "public",
    "metadata": {},
}


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


def _infer_vendor_relative(config: Mapping[str, Any], expected_relative: str) -> str:
    vendor_cfg = (
        config.get("generation", {}).get("vendor", {}) if isinstance(config, Mapping) else {}
    )
    files_cfg = vendor_cfg.get("files", []) if isinstance(vendor_cfg, Mapping) else []
    for entry in files_cfg:
        if not isinstance(entry, Mapping):
            continue
        template_name = entry.get("template")
        relative = entry.get("relative")
        if isinstance(relative, str):
            if Path(relative).name == Path(expected_relative).name:
                return relative
        if isinstance(template_name, str) and Path(template_name).name.startswith(
            Path(expected_relative).stem
        ):
            if isinstance(relative, str):
                return relative
    return expected_relative


def infer_vendor_primary_path(config: Mapping[str, Any]) -> str:
    """Return the vendor relative path used as the default output."""

    return _infer_vendor_relative(config, VENDOR_DATABASE_REL)


class DbPostgresModuleGenerator(BaseModuleGenerator):
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
        module = str(config.get("name", MODULE_NAME))
        module_version = str(config.get("version", "0.0.0"))
        project_defaults = config.get("defaults", {}) if isinstance(config, Mapping) else {}
        project_name = (
            str(project_defaults.get("project_name") or "RapidKit App").strip() or "RapidKit App"
        )
        project_slug = project_name.lower().replace(" ", "-")

        vendor_database_relative = _infer_vendor_relative(config, VENDOR_DATABASE_REL)
        vendor_health_relative = _infer_vendor_relative(config, VENDOR_HEALTH_REL)
        vendor_configuration_relative = _infer_vendor_relative(config, VENDOR_CONFIGURATION_REL)

        database_defaults = {
            **DATABASE_DEFAULTS,
            "metadata": dict(DATABASE_DEFAULTS.get("metadata", {})),
        }

        base_context: Dict[str, Any] = {
            "rapidkit_vendor_module": module,
            "rapidkit_vendor_version": module_version,
            "rapidkit_vendor_relative_path": vendor_database_relative,
            "rapidkit_vendor_database_relative": vendor_database_relative,
            "rapidkit_vendor_health_relative": vendor_health_relative,
            "rapidkit_vendor_configuration_relative": vendor_configuration_relative,
            "module_name": module,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "module_tier": MODULE_TIER,
            "module_slug": MODULE_SLUG,
            "python_output_relative": PYTHON_DATABASE_REL,
            "python_database_relative": PYTHON_DATABASE_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "python_config_relative": PYTHON_CONFIG_REL,
            "python_test_relative": PYTHON_TEST_REL,
            "nest_output_relative": NEST_SERVICE_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "nest_health_controller_relative": NEST_HEALTH_CONTROLLER_REL,
            "nest_health_module_relative": NEST_HEALTH_MODULE_REL,
            "nest_config_relative": NEST_CONFIG_REL,
            "nest_test_relative": NEST_TEST_REL,
            "base_module": "src",
            "project_name": project_name,
            "project_slug": project_slug,
            "database_defaults": database_defaults,
        }

        return base_context


def _create_generator() -> DbPostgresModuleGenerator:
    return DbPostgresModuleGenerator()


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
    expected_arg_count = 3
    if len(sys.argv) != expected_arg_count:
        available_plugins = list_available_plugins()
        available_names = list(available_plugins.keys())
        guidance = (
            "Usage: python -m modules.free.database.db_postgres.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.database.db_postgres.generate fastapi ../../examples/db_postgres\n"
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
    generator = DbPostgresModuleGenerator()

    try:
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.build_base_context(config)
        if version_updated:
            print(f"[db-postgres] Auto bumped module version to {config['version']}")
        renderer = generator.create_renderer()

        print(f"[db-postgres] Generating PostgreSQL module for {variant_name}...")
        generator.generate_vendor_files(config, target_dir, renderer, base_context)
        generator.generate_variant_files(variant_name, target_dir, renderer, base_context)
        print(f"[db-postgres] Successfully generated db_postgres module in {target_dir}")
    except GeneratorError as exc:
        print(f"[db-postgres] Generator Error: {exc.message}")
        if exc.context:
            print("Context:")
            for key, value in exc.context.items():
                print(f"  {key}: {value}")
        dep_hint = format_missing_dependencies(missing_optional_dependencies)
        if dep_hint:
            print(f"\n{dep_hint}")
        sys.exit(exc.exit_code)
    except (RuntimeError, OSError, yaml.YAMLError) as exc:
        print("[db-postgres] Generator failed with an unexpected error:")
        traceback = "\n".join(TracebackException.from_exception(exc).format())
        print(traceback)
        print(
            "[db-postgres] If this persists, run 'rapidkit modules doctor db_postgres' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
