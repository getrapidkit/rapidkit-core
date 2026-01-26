"""Shared fixtures for the File Storage module tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterator
from uuid import uuid4

import pytest

from modules.free.business.storage import generate


@pytest.fixture(scope="session")
def storage_module_path() -> Path:
    """Absolute path to the module sources."""

    return generate.MODULE_ROOT


@pytest.fixture
def rendered_storage_runtime(tmp_path: Path) -> ModuleType:
    """Render the vendor storage runtime template and import it."""

    renderer = generate.TemplateRenderer()
    config = generate.load_module_config()
    context = generate.build_base_context(config)

    template_path = generate.MODULE_ROOT / "templates/base/storage.py.j2"
    output_dir = tmp_path / "runtime"
    output_dir.mkdir(parents=True, exist_ok=True)
    runtime_file = output_dir / "storage_runtime.py"
    rendered = renderer.render(template_path, context)
    runtime_file.write_text(rendered, encoding="utf-8")

    module_name = f"rapidkit_storage_runtime_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, runtime_file)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to import rendered storage runtime")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def rendered_storage_health(tmp_path: Path) -> ModuleType:
    """Render the vendor health helper for the storage module."""

    renderer = generate.TemplateRenderer()
    config = generate.load_module_config()
    context = generate.build_base_context(config)

    template_path = generate.MODULE_ROOT / "templates/base/storage_health.py.j2"
    output_dir = tmp_path / "health"
    output_dir.mkdir(parents=True, exist_ok=True)
    health_file = output_dir / "storage_health.py"
    rendered = renderer.render(template_path, context)
    health_file.write_text(rendered, encoding="utf-8")

    module_name = f"rapidkit_storage_health_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, health_file)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to import rendered storage health module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def storage_config(rendered_storage_runtime: ModuleType, tmp_path: Path):
    """Instantiate a StorageConfig pointing to a temporary directory."""

    StorageConfig = rendered_storage_runtime.StorageConfig
    return StorageConfig(base_path=tmp_path)


@pytest.fixture
def storage_facade(rendered_storage_runtime: ModuleType, storage_config) -> Iterator[object]:
    """Yield a configured storage facade bound to a temporary directory."""

    storage_cls = getattr(rendered_storage_runtime, generate.MODULE_CLASS)
    facade = storage_cls(storage_config)
    yield facade
