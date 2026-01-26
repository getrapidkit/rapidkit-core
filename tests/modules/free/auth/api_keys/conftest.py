"""Shared pytest fixtures for Api Keys module tests."""

from __future__ import annotations

import importlib
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
