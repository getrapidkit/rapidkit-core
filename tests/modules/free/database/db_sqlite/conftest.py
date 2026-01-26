"""Shared pytest fixtures for Db Sqlite module tests."""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Iterator

import pytest

from modules.free.database.db_sqlite.generate import DbSqliteModuleGenerator
from modules.free.database.db_sqlite.overrides import DbSqliteOverrides

MODULE_IMPORT_PATH = "modules.free.database.db_sqlite"


@pytest.fixture(scope="session")
def module_generate() -> ModuleType:
    return importlib.import_module(f"{MODULE_IMPORT_PATH}.generate")


@pytest.fixture(scope="session")
def db_sqlite_generator() -> DbSqliteModuleGenerator:
    return DbSqliteModuleGenerator()


@pytest.fixture(scope="session")
def module_root(module_generate: ModuleType) -> Path:
    return Path(module_generate.__file__).resolve().parent


@pytest.fixture(scope="session")
def module_config(module_generate: ModuleType) -> dict[str, object]:
    return dict(module_generate.load_module_config())


@pytest.fixture(scope="session")
def module_docs(module_config: dict[str, object]) -> dict[str, object]:
    documentation = module_config.get("documentation", {})
    if isinstance(documentation, dict):
        return dict(documentation)
    return {}


def _write_package_module(destination: Path, source: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def _ensure_package(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    init_file = directory / "__init__.py"
    if not init_file.exists():
        init_file.write_text("", encoding="utf-8")


@dataclass
class GeneratedDbSqliteModules:
    base: ModuleType
    health: ModuleType
    types: ModuleType
    fastapi_runtime: ModuleType
    fastapi_routes: ModuleType
    package_name: str
    context: dict[str, object]


@pytest.fixture()
def generated_db_sqlite_modules(
    tmp_path: Path,
) -> Iterator[GeneratedDbSqliteModules]:
    overrides = DbSqliteOverrides()
    generator = DbSqliteModuleGenerator(overrides)
    config = generator.load_module_config()
    base_context = generator.build_base_context(config)
    enriched_context = generator.apply_base_context_overrides(base_context)
    renderer = generator.create_renderer()

    generator.generate_vendor_files(
        config,
        tmp_path,
        renderer,
        enriched_context,
    )
    generator.generate_variant_files(
        "fastapi",
        tmp_path,
        renderer,
        enriched_context,
    )

    vendor_root = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(enriched_context["rapidkit_vendor_module"])
        / str(enriched_context["rapidkit_vendor_version"])
        / "src"
    )
    vendor_module_root = vendor_root / "modules" / "free" / "database" / "db_sqlite"

    package_name = "generated_db_sqlite"
    package_root = tmp_path / package_name
    base_pkg = package_root / "base"
    vendor_database_pkg = base_pkg / "database"
    vendor_health_pkg = base_pkg / "health"
    vendor_types_pkg = base_pkg / "types"
    runtime_pkg = package_root / "runtime"

    for directory in (
        base_pkg,
        vendor_database_pkg,
        vendor_health_pkg,
        vendor_types_pkg,
        runtime_pkg,
    ):
        _ensure_package(directory)

    _write_package_module(
        vendor_database_pkg / "db_sqlite.py",
        vendor_module_root / "db_sqlite.py",
    )
    _write_package_module(
        base_pkg / "db_sqlite.py",
        vendor_module_root / "db_sqlite.py",
    )
    _write_package_module(
        vendor_health_pkg / "db_sqlite.py",
        vendor_root / "health" / "db_sqlite.py",
    )
    _write_package_module(
        vendor_types_pkg / "db_sqlite.py",
        vendor_module_root / "types" / "db_sqlite.py",
    )

    _write_package_module(
        runtime_pkg / "db_sqlite.py",
        tmp_path / "src" / "modules" / "free" / "database" / "db_sqlite" / "db_sqlite.py",
    )
    _write_package_module(
        runtime_pkg / "db_sqlite_routes.py",
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "database"
        / "db_sqlite"
        / "routers"
        / "db_sqlite.py",
    )

    sys_path_entry = str(tmp_path)
    sys.path.insert(0, sys_path_entry)

    original_types_module = sys.modules.get("types")
    original_health_module = sys.modules.get("health")
    original_database_module = sys.modules.get("database")
    proxy_types = ModuleType("types")
    if original_types_module is not None:
        proxy_types.__dict__.update(original_types_module.__dict__)
    proxy_types.__path__ = [str(vendor_types_pkg)]
    sys.modules["types"] = proxy_types

    proxy_health = ModuleType("health")
    if original_health_module is not None:
        proxy_health.__dict__.update(original_health_module.__dict__)
    proxy_health.__path__ = [str(vendor_health_pkg)]
    sys.modules["health"] = proxy_health

    proxy_database = ModuleType("database")
    if original_database_module is not None:
        proxy_database.__dict__.update(original_database_module.__dict__)
    proxy_database.__path__ = [str(vendor_database_pkg)]
    sys.modules["database"] = proxy_database

    base_module = importlib.import_module(f"{package_name}.base.database.db_sqlite")
    health_module = importlib.import_module(f"{package_name}.base.health.db_sqlite")
    types_module = importlib.import_module(f"{package_name}.base.types.db_sqlite")

    try:
        fastapi_runtime = importlib.import_module(f"{package_name}.runtime.db_sqlite")
        fastapi_routes = importlib.import_module(f"{package_name}.runtime.db_sqlite_routes")
    except ModuleNotFoundError as exc:
        if getattr(exc, "name", "") != "fastapi":
            raise
        fastapi_runtime = ModuleType(f"{package_name}.runtime.db_sqlite")
        fastapi_routes = ModuleType(f"{package_name}.runtime.db_sqlite_routes")

    yield GeneratedDbSqliteModules(
        base=base_module,
        health=health_module,
        types=types_module,
        fastapi_runtime=fastapi_runtime,
        fastapi_routes=fastapi_routes,
        package_name=package_name,
        context=dict(enriched_context),
    )

    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            sys.modules.pop(name, None)

    if original_types_module is not None:
        sys.modules["types"] = original_types_module
    else:
        sys.modules.pop("types", None)

    if original_health_module is not None:
        sys.modules["health"] = original_health_module
    else:
        sys.modules.pop("health", None)

    if original_database_module is not None:
        sys.modules["database"] = original_database_module
    else:
        sys.modules.pop("database", None)

    if sys_path_entry in sys.path:
        sys.path.remove(sys_path_entry)
