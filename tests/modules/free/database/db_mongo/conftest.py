"""Shared pytest fixtures for Db Mongo module tests."""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Iterator

import pytest

from modules.free.database.db_mongo.generate import DbMongoModuleGenerator
from modules.free.database.db_mongo.overrides import DbMongoOverrides

MODULE_IMPORT_PATH = "modules.free.database.db_mongo"


@pytest.fixture(scope="session")
def module_generate() -> ModuleType:
    return importlib.import_module(f"{MODULE_IMPORT_PATH}.generate")


@pytest.fixture(scope="session")
def db_mongo_generator() -> DbMongoModuleGenerator:
    return DbMongoModuleGenerator()


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
    init_path = directory / "__init__.py"
    if not init_path.exists():
        init_path.write_text("", encoding="utf-8")


@dataclass
class GeneratedDbMongoModules:
    base: ModuleType
    health: ModuleType
    types: ModuleType
    fastapi_runtime: ModuleType
    fastapi_routes: ModuleType
    package_name: str
    context: dict[str, object]


@pytest.fixture()
def generated_db_mongo_modules(tmp_path: Path) -> Iterator[GeneratedDbMongoModules]:
    overrides = DbMongoOverrides()
    generator = DbMongoModuleGenerator(overrides)
    config = generator.load_module_config()
    base_context = generator.build_base_context(config)
    enriched_context = generator.apply_base_context_overrides(base_context)
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, tmp_path, renderer, enriched_context)
    generator.generate_variant_files("fastapi", tmp_path, renderer, enriched_context)

    vendor_top = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(enriched_context["rapidkit_vendor_module"])
        / str(enriched_context["rapidkit_vendor_version"])
    )
    vendor_root = vendor_top / "src" / "modules" / "free" / "database" / "db_mongo"
    vendor_health_root = vendor_top / "src" / "health"

    package_name = "generated_db_mongo"
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
        vendor_database_pkg / "db_mongo.py",
        vendor_root / "db_mongo.py",
    )
    _write_package_module(
        base_pkg / "db_mongo.py",
        vendor_root / "db_mongo.py",
    )
    _write_package_module(
        vendor_health_pkg / "db_mongo.py",
        vendor_health_root / "db_mongo.py",
    )
    _write_package_module(
        vendor_types_pkg / "db_mongo.py",
        vendor_root / "types" / "db_mongo.py",
    )
    _write_package_module(
        runtime_pkg / "db_mongo.py",
        tmp_path / "src" / "modules" / "free" / "database" / "db_mongo" / "db_mongo.py",
    )
    _write_package_module(
        runtime_pkg / "db_mongo_routes.py",
        tmp_path / "src" / "modules" / "free" / "database" / "db_mongo" / "routers" / "db_mongo.py",
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

    base_module = importlib.import_module(f"{package_name}.base.database.db_mongo")
    health_module = importlib.import_module(f"{package_name}.base.health.db_mongo")
    types_module = importlib.import_module(f"{package_name}.base.types.db_mongo")
    fastapi_runtime = importlib.import_module(f"{package_name}.runtime.db_mongo")
    fastapi_routes = importlib.import_module(f"{package_name}.runtime.db_mongo_routes")

    yield GeneratedDbMongoModules(
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
