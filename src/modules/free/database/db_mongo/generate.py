#!/usr/bin/env python3
"""Unified module generator for Db Mongo."""

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
from .overrides import DbMongoOverrides

MODULE_ROOT = Path(__file__).parent
PROJECT_ROOT = BaseModuleGenerator.detect_project_root(MODULE_ROOT)

MODULE_NAME = "db_mongo"
MODULE_CLASS = "DbMongo"
MODULE_TITLE = "Db Mongo"
MODULE_TIER = "free"
MODULE_CATEGORY = "database"
MODULE_CATEGORY_DISPLAY = "database"
MODULE_KEBAB = "db-mongo"
MODULE_IMPORT_PATH = "modules.free.database.db_mongo"
MODULE_BASE = "src/modules/free/database/db_mongo"
VENDOR_RUNTIME_REL = f"{MODULE_BASE}/db_mongo.py"
VENDOR_HEALTH_REL = f"{MODULE_BASE}/health/db_mongo.py"
VENDOR_TYPES_REL = f"{MODULE_BASE}/types/db_mongo.py"
VENDOR_CONFIGURATION_REL = "nestjs/configuration.js"

PYTHON_RUNTIME_REL = f"{MODULE_BASE}/db_mongo.py"
PYTHON_HEALTH_REL = f"{MODULE_BASE}/health/db_mongo.py"
PYTHON_ROUTES_REL = f"{MODULE_BASE}/routers/db_mongo.py"
PYTHON_CONFIG_REL = "config/database/db_mongo.yaml"
PYTHON_TEST_REL = "tests/modules/integration/database/test_db_mongo_integration.py"

NEST_BASE = f"{MODULE_BASE}/db-mongo"
NEST_SERVICE_REL = f"{NEST_BASE}/db-mongo.service.ts"
NEST_CONTROLLER_REL = f"{NEST_BASE}/db-mongo.controller.ts"
NEST_MODULE_REL = f"{NEST_BASE}/db-mongo.module.ts"
NEST_CONFIGURATION_REL = f"{NEST_BASE}/db-mongo.configuration.ts"
NEST_HEALTH_CONTROLLER_REL = f"{MODULE_BASE}/health/db-mongo-health.controller.ts"
NEST_HEALTH_MODULE_REL = f"{MODULE_BASE}/health/db-mongo-health.module.ts"
NEST_TEST_REL = "tests/modules/integration/database/db_mongo.integration.spec.ts"


class GeneratorError(ModuleGeneratorError):
    """Explicit generator failure carrying helpful metadata."""

    def __init__(
        self,
        message: str,
        *,
        exit_code: int = 1,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, context=context or {})
        self.exit_code = exit_code


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _coerce_int(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_float(value: Any, default: float) -> float:
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_str(value: Any, default: str) -> str:
    if value is None:
        return default
    return str(value)


def _coerce_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if isinstance(value, str):
        segments = [segment.strip() for segment in value.split(",") if segment.strip()]
        return segments
    return []


def _defaults_from_config(config: Mapping[str, Any]) -> Dict[str, Any]:
    defaults = config.get("defaults")
    if not isinstance(defaults, Mapping):
        defaults = {}

    connection = defaults.get("connection")
    if not isinstance(connection, Mapping):
        connection = {}

    health = defaults.get("health")
    if not isinstance(health, Mapping):
        health = {}

    pool = defaults.get("pool")
    if not isinstance(pool, Mapping):
        pool = {}

    security = defaults.get("security")
    if not isinstance(security, Mapping):
        security = {}

    return {
        "enabled": _coerce_bool(defaults.get("enabled", True), True),
        "connection": {
            "uri": _coerce_str(
                connection.get("primary_uri", "mongodb://localhost:27017"),
                "mongodb://localhost:27017",
            ),
            "database": _coerce_str(connection.get("database", "rapidkit"), "rapidkit"),
            "app_name": _coerce_str(
                connection.get("app_name", "rapidkit-db-mongo"), "rapidkit-db-mongo"
            ),
            "auth_source": _coerce_str(connection.get("auth_source", "admin"), "admin"),
            "username": connection.get("username"),
            "password": connection.get("password"),
            "replica_set": connection.get("replica_set"),
            "read_preference": _coerce_str(connection.get("read_preference", "primary"), "primary"),
            "compressors": _coerce_list(connection.get("compressors", [])),
            "retry_reads": _coerce_bool(connection.get("retry_reads", True), True),
            "retry_writes": _coerce_bool(connection.get("retry_writes", True), True),
            "connect_timeout_ms": _coerce_int(connection.get("connect_timeout_ms", 5000), 5000),
            "server_selection_timeout_ms": _coerce_int(
                connection.get("server_selection_timeout_ms", 8000), 8000
            ),
            "max_idle_time_ms": _coerce_int(connection.get("max_idle_time_ms", 120000), 120000),
        },
        "pool": {
            "min_size": _coerce_int(pool.get("min_pool_size", 0), 0),
            "max_size": _coerce_int(pool.get("max_pool_size", 20), 20),
        },
        "security": {
            "tls": _coerce_bool(security.get("tls", False), False),
            "tls_allow_invalid_certificates": _coerce_bool(
                security.get("tls_allow_invalid_certificates", False),
                False,
            ),
        },
        "health": {
            "ping_timeout_ms": _coerce_int(health.get("ping_timeout_ms", 1500), 1500),
            "metrics": _coerce_bool(health.get("metrics", True), True),
        },
    }


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
        if isinstance(template_name, str):
            template_basename = Path(template_name).name
            if template_basename.startswith(
                Path(expected_relative).stem
            ) or template_basename.endswith(f"{Path(expected_relative).name}.j2"):
                if isinstance(relative, str):
                    return relative
    return expected_relative


def infer_vendor_settings_path(config: Mapping[str, Any]) -> str:
    return _infer_vendor_relative(config, VENDOR_RUNTIME_REL)


class DbMongoModuleGenerator(BaseModuleGenerator):
    """Module generator that embraces the shared plugin architecture."""

    def __init__(self, overrides: Optional[DbMongoOverrides] = None) -> None:
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
            self._overrides = DbMongoOverrides(MODULE_ROOT)

    @property
    def overrides(self) -> DbMongoOverrides:
        if self._overrides is None:
            raise RuntimeError("Db Mongo overrides not initialised")
        return self._overrides

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, Any]:
        defaults = _defaults_from_config(config)
        connection = defaults["connection"]
        pool = defaults["pool"]
        security = defaults["security"]
        health = defaults["health"]

        module = str(config.get("name", MODULE_NAME))
        version = str(config.get("version", "0.0.0"))

        vendor_runtime_relative = infer_vendor_settings_path(config)
        vendor_health_relative = _infer_vendor_relative(config, VENDOR_HEALTH_REL)
        vendor_types_relative = _infer_vendor_relative(config, VENDOR_TYPES_REL)
        vendor_configuration_relative = _infer_vendor_relative(config, VENDOR_CONFIGURATION_REL)

        return {
            "rapidkit_vendor_module": module,
            "rapidkit_vendor_version": version,
            "rapidkit_vendor_relative_path": vendor_runtime_relative,
            "rapidkit_vendor_runtime_relative": vendor_runtime_relative,
            "rapidkit_vendor_health_relative": vendor_health_relative,
            "rapidkit_vendor_types_relative": vendor_types_relative,
            "rapidkit_vendor_configuration_relative": vendor_configuration_relative,
            "module_name": module,
            "module_class_name": MODULE_CLASS,
            "module_title": MODULE_TITLE,
            "python_output_relative": PYTHON_RUNTIME_REL,
            "python_runtime_relative": PYTHON_RUNTIME_REL,
            "python_health_relative": PYTHON_HEALTH_REL,
            "python_routes_relative": PYTHON_ROUTES_REL,
            "python_config_relative": PYTHON_CONFIG_REL,
            "python_test_relative": PYTHON_TEST_REL,
            "nest_output_relative": NEST_SERVICE_REL,
            "nest_service_relative": NEST_SERVICE_REL,
            "nest_controller_relative": NEST_CONTROLLER_REL,
            "nest_module_relative": NEST_MODULE_REL,
            "nest_configuration_relative": NEST_CONFIGURATION_REL,
            "nest_health_controller_relative": NEST_HEALTH_CONTROLLER_REL,
            "nest_health_module_relative": NEST_HEALTH_MODULE_REL,
            "nest_test_relative": NEST_TEST_REL,
            "module_tier": MODULE_TIER,
            "module_kebab": MODULE_KEBAB,
            "module_category": MODULE_CATEGORY,
            "module_category_display": MODULE_CATEGORY_DISPLAY,
            "module_import_path": MODULE_IMPORT_PATH,
            "enabled_by_default": defaults["enabled"],
            "default_connection_uri": connection["uri"],
            "default_database_name": connection["database"],
            "default_app_name": connection["app_name"],
            "default_auth_source": connection["auth_source"],
            "default_username": connection.get("username"),
            "default_password": connection.get("password"),
            "default_replica_set": connection.get("replica_set"),
            "default_read_preference": connection["read_preference"],
            "default_compressors": connection["compressors"],
            "default_retry_reads": connection["retry_reads"],
            "default_retry_writes": connection["retry_writes"],
            "default_connect_timeout_ms": connection["connect_timeout_ms"],
            "default_server_selection_timeout_ms": connection["server_selection_timeout_ms"],
            "default_max_idle_time_ms": connection["max_idle_time_ms"],
            "default_pool_min_size": pool["min_size"],
            "default_pool_max_size": pool["max_size"],
            "default_tls_enabled": security["tls"],
            "default_tls_allow_invalid_certificates": security["tls_allow_invalid_certificates"],
            "default_health_timeout_ms": health["ping_timeout_ms"],
            "default_collect_metrics": health["metrics"],
            "mongo_defaults": {
                "connection_uri": connection["uri"],
                "database": connection["database"],
                "app_name": connection["app_name"],
                "auth_source": connection["auth_source"],
                "username": connection.get("username"),
                "password": connection.get("password"),
                "replica_set": connection.get("replica_set"),
                "read_preference": connection["read_preference"],
                "compressors": connection["compressors"],
                "retry_reads": connection["retry_reads"],
                "retry_writes": connection["retry_writes"],
                "connect_timeout_ms": connection["connect_timeout_ms"],
                "server_selection_timeout_ms": connection["server_selection_timeout_ms"],
                "max_idle_time_ms": connection["max_idle_time_ms"],
                "min_pool_size": pool["min_size"],
                "max_pool_size": pool["max_size"],
                "tls": security["tls"],
                "tls_allow_invalid_certificates": security["tls_allow_invalid_certificates"],
            },
            "health_defaults": {
                "ping_timeout_ms": health["ping_timeout_ms"],
                "metrics": health["metrics"],
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


def _create_generator(overrides: Optional[DbMongoOverrides] = None) -> DbMongoModuleGenerator:
    return DbMongoModuleGenerator(overrides=overrides)


def load_module_config() -> Dict[str, Any]:
    generator = _create_generator()
    config = generator.load_module_config()
    return dict(config)


def build_base_context(config: Mapping[str, Any]) -> Dict[str, Any]:
    generator = _create_generator()
    return dict(generator.build_base_context(config))


def generate_vendor_files(
    config: Mapping[str, Any],
    target_dir: Path,
    renderer: TemplateRenderer,
    context: Mapping[str, Any],
    overrides: Optional[DbMongoOverrides] = None,
) -> None:
    generator = _create_generator(overrides=overrides)
    generator.generate_vendor_files(config, target_dir, renderer, context)


def generate_variant_files(
    config: Mapping[str, Any],
    variant_name: str,
    target_dir: Path,
    renderer: TemplateRenderer,
    context: Mapping[str, Any],
    overrides: Optional[DbMongoOverrides] = None,
) -> None:
    _ = config  # Preserve backwards-compatible signature
    generator = _create_generator(overrides=overrides)
    generator.generate_variant_files(variant_name, target_dir, renderer, context)


def main() -> None:
    expected_arg_count = 3
    if len(sys.argv) != expected_arg_count:
        available_plugins = list_available_plugins()
        available_names = ", ".join(available_plugins.keys()) or "<none>"
        guidance = (
            "Usage: python -m modules.free.database.db_mongo.generate <framework> <target_dir>\n"
            "Example: python -m modules.free.database.db_mongo.generate fastapi ../../examples/db_mongo\n"
            f"Available frameworks: {available_names}"
        )
        raise GeneratorError(
            guidance,
            exit_code=2,
            context={"provided_args": sys.argv[1:], "available_frameworks": available_plugins},
        )

    variant_name = sys.argv[1]
    target_dir = Path(sys.argv[2]).resolve()

    generator = DbMongoModuleGenerator()
    missing_optional_dependencies: Dict[str, str] = {}

    try:
        config = generator.load_module_config()
        config, version_updated = ensure_version_consistency(config, module_root=MODULE_ROOT)
        base_context = generator.build_base_context(config)
        enriched_context = generator.apply_base_context_overrides(base_context)
        if version_updated:
            print(f"Auto bumped db_mongo module version to {config['version']}")
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
            "💡 If this persists, run 'rapidkit modules doctor db_mongo' or reinstall dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()


__all__ = [
    "DbMongoModuleGenerator",
    "load_module_config",
    "build_base_context",
    "generate_vendor_files",
    "generate_variant_files",
    "main",
]
