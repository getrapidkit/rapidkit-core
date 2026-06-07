"""Shared pytest fixtures for Api Keys module tests."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

MODULE_IMPORT_PATH = "modules.free.auth.api_keys"


@pytest.fixture(scope="session")
def module_generate() -> ModuleType:
    return importlib.import_module(f"{MODULE_IMPORT_PATH}.generate")


@pytest.fixture(scope="session")
def api_keys_generator(module_generate: ModuleType):
    return module_generate.ApiKeysModuleGenerator()


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


def _load_generated_package(package_name: str, module_dir: Path, module_file: str) -> ModuleType:
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            sys.modules.pop(name, None)

    package = ModuleType(package_name)
    package.__path__ = [str(module_dir)]  # type: ignore[attr-defined]
    sys.modules[package_name] = package

    spec = importlib.util.spec_from_file_location(
        f"{package_name}.api_keys",
        module_dir / module_file,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated Api Keys runtime from {module_dir}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def rendered_api_keys(api_keys_generator, module_config, tmp_path: Path) -> dict[str, object]:
    renderer = api_keys_generator.create_renderer()
    context = api_keys_generator.apply_base_context_overrides(
        api_keys_generator.build_base_context(module_config)
    )

    api_keys_generator.generate_variant_files("fastapi", tmp_path, renderer, context)
    module_dir = tmp_path / "src/modules/free/auth/api_keys"

    return {
        "root": tmp_path,
        "runtime": _load_generated_package(
            "generated_api_keys",
            module_dir,
            "api_keys.py",
        ),
        "module_dir": module_dir,
    }
