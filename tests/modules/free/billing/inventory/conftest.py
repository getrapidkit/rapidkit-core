"""Shared pytest fixtures for Inventory module tests."""

from __future__ import annotations

import contextlib
import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterator

import pytest

MODULE_IMPORT_PATH = "src.modules.free.billing.inventory"


@pytest.fixture(scope="session")
def module_generate() -> ModuleType:
    return importlib.import_module(f"{MODULE_IMPORT_PATH}.generate")


@pytest.fixture(scope="session")
def module_root(module_generate: ModuleType) -> Path:
    module_file = getattr(module_generate, "__file__", None)
    if module_file is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Inventory module missing __file__ attribute")
    return Path(module_file).resolve().parent


@pytest.fixture(scope="session")
def module_config(module_generate: ModuleType) -> dict[str, object]:
    return dict(module_generate.load_module_config())


@pytest.fixture(scope="session")
def module_docs(module_config: dict[str, object]) -> dict[str, object]:
    documentation = module_config.get("documentation", {})
    if isinstance(documentation, dict):
        return dict(documentation)
    return {}


@pytest.fixture(scope="session")
def inventory_generator(module_generate: ModuleType):
    return module_generate.InventoryModuleGenerator()


@pytest.fixture(scope="session")
def base_context(inventory_generator, module_config):
    context = inventory_generator.build_base_context(module_config)
    return inventory_generator.apply_base_context_overrides(context)


@pytest.fixture(scope="session")
def generated_bundle(
    tmp_path_factory: pytest.TempPathFactory,
    inventory_generator,
    module_config,
    base_context,
):
    target = tmp_path_factory.mktemp("inventory-module")
    renderer = inventory_generator.create_renderer()
    inventory_generator.generate_vendor_files(module_config, target, renderer, base_context)
    inventory_generator.generate_variant_files("fastapi", target, renderer, base_context)
    inventory_generator.generate_variant_files("nestjs", target, renderer, base_context)
    return {
        "target": target,
        "context": base_context,
    }


def _prepend_sys_path(path: Path, *, module_prefixes: tuple[str, ...] = ("src",)) -> Iterator[Path]:
    resolved_path = path.resolve()
    path_str = str(resolved_path)
    preserved_modules: dict[str, ModuleType] = {}

    for prefix in module_prefixes:
        for name, module in list(sys.modules.items()):
            if name == prefix or name.startswith(f"{prefix}."):
                preserved_modules.setdefault(name, module)
                sys.modules.pop(name, None)

    sys.path.insert(0, path_str)

    before_modules = set(sys.modules.keys())
    augmented_pkg_paths: list[tuple[object, str]] = []

    def _extend_src_namespace(candidate: Path) -> None:
        src_pkg = sys.modules.get("src")
        if src_pkg is None:
            return
        pkg_path = getattr(src_pkg, "__path__", None)
        if pkg_path is None:
            return
        candidate_str = str(candidate)
        if candidate_str not in pkg_path:
            pkg_path.insert(0, candidate_str)
            augmented_pkg_paths.append((src_pkg, candidate_str))

    if resolved_path.name == "src":
        _extend_src_namespace(resolved_path)
    else:
        candidate_src = resolved_path / "src"
        if candidate_src.exists():
            _extend_src_namespace(candidate_src)

    try:
        yield resolved_path
    finally:
        with contextlib.suppress(ValueError):  # pragma: no cover - defensive removal
            sys.path.remove(path_str)

        for pkg, candidate in augmented_pkg_paths:
            pkg_path = getattr(pkg, "__path__", None)
            if not pkg_path:
                continue
            with contextlib.suppress(ValueError):  # pragma: no cover - defensive removal
                pkg_path.remove(candidate)

        newly_loaded = set(sys.modules.keys()) - before_modules
        for name in newly_loaded:
            loaded_module = sys.modules.get(name)
            if loaded_module is None:
                continue
            try:
                module_paths: list[Path] = []
                module_file = getattr(loaded_module, "__file__", None)
                if module_file:
                    module_paths.append(Path(module_file).resolve())

                module_path_attr = getattr(loaded_module, "__path__", None)
                if module_path_attr:
                    module_paths.extend([Path(entry).resolve() for entry in module_path_attr])
            except KeyError:
                # Namespace packages can race during teardown; ignore missing modules
                continue

            for candidate in module_paths:
                try:
                    candidate.relative_to(resolved_path)
                except ValueError:
                    continue
                else:
                    sys.modules.pop(name, None)
                    break

        sys.modules.update(preserved_modules)


@pytest.fixture()
def vendor_import_path(generated_bundle):
    target: Path = generated_bundle["target"]
    context = generated_bundle["context"]
    vendor_path = (
        target
        / ".rapidkit"
        / "vendor"
        / context["rapidkit_vendor_module"]
        / context["rapidkit_vendor_version"]
    )
    yield from _prepend_sys_path(vendor_path)


@pytest.fixture()
def fastapi_import_path(generated_bundle):
    target: Path = generated_bundle["target"]
    yield from _prepend_sys_path(target)


@pytest.fixture()
def _vendor_import_path(vendor_import_path: Path):
    yield vendor_import_path


@pytest.fixture()
def _fastapi_import_path(fastapi_import_path: Path):
    yield fastapi_import_path


@pytest.fixture()
def vendor_inventory_module(
    _vendor_import_path,
) -> ModuleType:  # noqa: PT004 - depends on fixture for sys.path
    module = importlib.import_module("src.modules.free.billing.inventory.inventory")
    importlib.reload(module)
    return module


@pytest.fixture()
def inventory_service(vendor_inventory_module: ModuleType):
    InventoryService = vendor_inventory_module.InventoryService
    return InventoryService()
