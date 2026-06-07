from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from modules.free.ai.llm_gateway.generate import LlmGatewayModuleGenerator


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_free_ai_llm_gateway_generates_and_completes_offline(tmp_path: Path) -> None:
    generator = LlmGatewayModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor_path = (
        tmp_path / ".rapidkit/vendor" / config["name"] / config["version"] / "src/ai/llm_gateway.py"
    )
    vendor = _load_module("integration_llm_gateway_vendor", vendor_path)

    gateway = vendor.LlmGateway()
    response = gateway.complete(
        vendor.LlmGatewayRequest(
            prompt="Draft a marketplace release note",
            tenant_id="tenant-1",
            user_id="user-1",
        )
    )

    assert response.provider == "local"
    assert response.metadata["offline"] is True
    assert gateway.usage_snapshot()["requests"] == 1
