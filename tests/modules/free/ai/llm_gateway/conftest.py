import importlib.util
import sys
from pathlib import Path

import pytest

from modules.free.ai.llm_gateway.generate import LlmGatewayModuleGenerator


@pytest.fixture(name="module_test_context")
def module_test_context_fixture(tmp_path: Path) -> dict[str, object]:
    """Provide an isolated workspace for Llm Gateway module tests."""

    working_dir = tmp_path / "llm_gateway"
    working_dir.mkdir(parents=True, exist_ok=True)
    return {
        "module_name": "llm_gateway",
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
def rendered_llm_gateway(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    generator = LlmGatewayModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, tmp_path, renderer, context)
    generator.generate_variant_files("fastapi", tmp_path, renderer, context)

    vendor_root = tmp_path / ".rapidkit" / "vendor"
    monkeypatch.setenv("RAPIDKIT_VENDOR_ROOT", str(vendor_root))

    runtime_path = tmp_path / "src" / "ai" / "llm_gateway.py"
    vendor_path = vendor_root / config["name"] / config["version"] / "src" / "ai" / "llm_gateway.py"

    return {
        "root": tmp_path,
        "runtime": _load_module("generated_llm_gateway_runtime", runtime_path),
        "vendor": _load_module("generated_llm_gateway_vendor", vendor_path),
    }
