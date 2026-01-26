"""Shared pytest fixtures for Cart module tests."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import Dict, Iterator

import pytest

MODULE_IMPORT_PATH = "src.modules.free.billing.cart"


@pytest.fixture(scope="session")
def module_generate() -> ModuleType:
    # Full-suite runs can leave `src.modules*` in an inconsistent state
    # (e.g. child packages present without parents) due to other tests
    # temporarily evicting/reloading generated runtimes. Ensure a clean import
    # chain for this session-scoped fixture.
    for name in list(sys.modules.keys()):
        if name == "src.modules" or name.startswith("src.modules."):
            sys.modules.pop(name, None)
    return importlib.import_module(f"{MODULE_IMPORT_PATH}.generate")


@pytest.fixture(scope="session")
def cart_module_generator(module_generate: ModuleType):
    return module_generate.CartModuleGenerator()


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


@pytest.fixture()
def mutable_workdir(tmp_path) -> Path:
    return tmp_path


@pytest.fixture()
def rendered_cart_runtime(
    cart_module_generator,
    module_config: Dict[str, object],
    mutable_workdir: Path,
) -> Iterator[Path]:
    renderer = cart_module_generator.create_renderer()
    base_context = cart_module_generator.apply_base_context_overrides(
        cart_module_generator.build_base_context(module_config)
    )
    cart_module_generator.generate_vendor_files(
        module_config, mutable_workdir, renderer, base_context
    )
    cart_module_generator.generate_variant_files("fastapi", mutable_workdir, renderer, base_context)
    yield mutable_workdir


@pytest.fixture()
def generated_modules(rendered_cart_runtime: Path) -> Iterator[Dict[str, ModuleType]]:
    # Ensure generated 'src' packages take precedence over any already-loaded
    # project-level 'src' package. Temporarily remove entries to force import
    # resolution from the rendered runtime directory.
    purge_candidates = [
        "src",
        "src.health",
        "src.health.cart",
        "src.modules",
        "src.modules.free",
        "src.modules.free.billing",
        "src.modules.free.billing.cart",
        "src.modules.free.billing.cart.cart",
        "src.modules.free.billing.cart.types",
        "src.modules.free.billing.cart.routers",
    ]
    removed: Dict[str, ModuleType] = {}
    for name in purge_candidates:
        existing = sys.modules.pop(name, None)
        if existing is not None:
            removed[name] = existing
    sys.path.insert(0, str(rendered_cart_runtime))
    try:
        runtime = importlib.import_module("src.modules.free.billing.cart.cart")
        types = importlib.import_module("src.modules.free.billing.cart.types.cart")
        health = importlib.import_module("src.health.cart")
        yield {"runtime": runtime, "types": types, "health": health}
    finally:
        sys.path.pop(0)
        for name in [
            "src.modules.free.billing.cart.cart",
            "src.modules.free.billing.cart.types.cart",
            "src.modules.free.billing.cart.routers.cart",
            "src.health.cart",
        ]:
            sys.modules.pop(name, None)
        # Restore any previously-imported src modules
        for name, module in removed.items():
            sys.modules[name] = module
