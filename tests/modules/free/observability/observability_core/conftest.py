"""Shared pytest fixtures for Observability Core module tests."""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Iterator

import pytest

MODULE_IMPORT_CANDIDATES = (
    "modules.free.observability.core",
    "modules.free.observability.observability_core",
)


def _resolve_import_path() -> str:
    for candidate in MODULE_IMPORT_CANDIDATES:
        try:
            importlib.import_module(f"{candidate}.generate")
        except ModuleNotFoundError:
            continue
        return candidate
    raise ModuleNotFoundError(
        "Unable to locate observability_core module in known import locations"
    )


MODULE_IMPORT_PATH = _resolve_import_path()


@pytest.fixture(scope="session")
def module_generate() -> ModuleType:
    return importlib.import_module(f"{MODULE_IMPORT_PATH}.generate")


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
class GeneratedObservabilityModules:
    base: ModuleType
    types: ModuleType
    health: ModuleType
    fastapi_runtime: ModuleType
    fastapi_routes: ModuleType
    package_name: str
    context: dict[str, object]


@pytest.fixture()
def generated_observability_modules(
    tmp_path: Path,
    module_generate: ModuleType,
) -> Iterator[GeneratedObservabilityModules]:
    pytest.importorskip("pydantic")
    generator = module_generate.ObservabilityModuleGenerator()
    config = generator.load_module_config()
    renderer = generator.create_renderer()
    base_context = generator.apply_base_context_overrides(generator.build_base_context(config))

    generator.generate_vendor_files(config, tmp_path, renderer, base_context)
    generator.generate_variant_files("fastapi", tmp_path, renderer, base_context)

    vendor_root = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(base_context["rapidkit_vendor_module"])
        / str(base_context["rapidkit_vendor_version"])
    )

    package_name = "generated_observability"
    package_root = tmp_path / package_name
    _ensure_package(package_root)
    base_dir = package_root / "base"
    observability_dir = package_root / "observability"
    _ensure_package(base_dir)
    _ensure_package(observability_dir)
    routers_dir = observability_dir / "routers"
    _ensure_package(routers_dir)
    types_dir = observability_dir / "types"
    _ensure_package(types_dir)

    _write_package_module(
        base_dir / "observability_core.py",
        vendor_root / "src/modules/free/observability/core/observability_core.py",
    )
    _write_package_module(
        base_dir / "observability_core_types.py",
        vendor_root / "src/modules/free/observability/core/observability_core_types.py",
    )
    _write_package_module(
        base_dir / "observability_core_health.py",
        vendor_root / "src/health/observability_core.py",
    )
    _write_package_module(
        observability_dir / "observability_core.py",
        tmp_path / "src/modules/free/observability/core/observability_core.py",
    )
    _write_package_module(
        observability_dir / "observability_core_types.py",
        vendor_root / "src/modules/free/observability/core/observability_core_types.py",
    )
    _write_package_module(
        types_dir / "observability_core.py",
        vendor_root / "src/modules/free/observability/core/observability_core_types.py",
    )
    _write_package_module(
        observability_dir / "observability_core_health.py",
        vendor_root / "src/health/observability_core.py",
    )
    _write_package_module(
        routers_dir / "observability_core.py",
        tmp_path / "src/modules/free/observability/core/routers/observability_core.py",
    )

    sys_path_entry = str(tmp_path)
    sys.path.insert(0, sys_path_entry)

    base_module = importlib.import_module(f"{package_name}.base.observability_core")
    types_module = importlib.import_module(f"{package_name}.base.observability_core_types")
    health_module = importlib.import_module(f"{package_name}.base.observability_core_health")
    fastapi_runtime = importlib.import_module(f"{package_name}.observability.observability_core")
    fastapi_routes = importlib.import_module(
        f"{package_name}.observability.routers.observability_core"
    )

    yield GeneratedObservabilityModules(
        base=base_module,
        types=types_module,
        health=health_module,
        fastapi_runtime=fastapi_runtime,
        fastapi_routes=fastapi_routes,
        package_name=package_name,
        context=dict(base_context),
    )

    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            sys.modules.pop(name, None)

    if sys_path_entry in sys.path:
        sys.path.remove(sys_path_entry)
