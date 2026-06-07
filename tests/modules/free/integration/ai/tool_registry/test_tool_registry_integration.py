import importlib.util
import sys
from pathlib import Path

from modules.free.ai.tool_registry.generate import ToolRegistryModuleGenerator


def _load_module(name: str, path: Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_free_ai_tool_registry_generated_vendor_smoke(tmp_path: Path) -> None:
    generator = ToolRegistryModuleGenerator()
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
        / "ai"
        / "tool_registry.py"
    )
    vendor = _load_module("generated_tool_registry_integration_vendor", vendor_path)

    runtime = vendor.ToolRegistry()

    assert runtime.health_check()["module"] == "tool_registry"
