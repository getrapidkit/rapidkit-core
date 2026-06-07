import importlib.util
import sys
from pathlib import Path

from modules.free.business.connector_pack_library.generate import (
    ConnectorPackLibraryModuleGenerator,
)


def _load_vendor(path: Path) -> object:
    spec = importlib.util.spec_from_file_location("integration_connector_pack_library_vendor", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated vendor from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_connector_pack_library_integration_runtime_smoke(tmp_path: Path) -> None:
    generator = ConnectorPackLibraryModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()
    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor = _load_vendor(
        tmp_path
        / ".rapidkit"
        / "vendor"
        / "connector_pack_library"
        / "0.1.3"
        / "src/business/connector_pack_library.py"
    )
    console = vendor.ConnectorPackLibrary()
    pack = console.register_pack(
        key="stripe", provider="stripe", display_name="Stripe", scopes=("payments:read",)
    )
    console.install_pack(pack.key, actor_id="admin")

    assert console.health()["installed"] == 1
