import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.fixture(name="module_test_context")
def module_test_context_fixture(tmp_path: Path) -> dict[str, object]:
    """Provide an isolated workspace for Connector Pack Library module tests."""

    working_dir = tmp_path / "connector_pack_library"
    working_dir.mkdir(parents=True, exist_ok=True)
    return {
        "module_name": "connector_pack_library",
        "workspace": working_dir,
        "context_file": working_dir / "context.json",
    }


def _load_module(name: str, path: Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def rendered_connector_pack_library(tmp_path: Path) -> dict[str, object]:
    from modules.free.business.connector_pack_library.generate import (
        ConnectorPackLibraryModuleGenerator,
    )

    generator = ConnectorPackLibraryModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()
    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor_path = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / config["name"]
        / config["version"]
        / "src"
        / "business"
        / "connector_pack_library.py"
    )
    return {
        "root": tmp_path,
        "vendor": _load_module("generated_connector_pack_library_vendor", vendor_path),
    }
