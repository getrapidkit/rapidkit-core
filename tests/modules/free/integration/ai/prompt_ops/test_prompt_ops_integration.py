import importlib.util
import sys
from pathlib import Path

from modules.free.ai.prompt_ops.generate import PromptOpsModuleGenerator


def _load_module(name: str, path: Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_free_ai_prompt_ops_generated_vendor_smoke(tmp_path: Path) -> None:
    generator = PromptOpsModuleGenerator()
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
        / "prompt_ops.py"
    )
    vendor = _load_module("generated_prompt_ops_integration_vendor", vendor_path)

    runtime = vendor.PromptOps()

    assert runtime.health_check()["module"] == "prompt_ops"
