from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from modules.free.ai.ai_assistant.generate import AiAssistantModuleGenerator


def _load_package_module(package_name: str, module_dir: Path, module_file: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            sys.modules.pop(name, None)

    package = ModuleType(package_name)
    package.__path__ = [str(module_dir)]  # type: ignore[attr-defined]
    sys.modules[package_name] = package

    spec = importlib.util.spec_from_file_location(
        f"{package_name}.ai_assistant",
        module_dir / module_file,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {module_dir}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_free_ai_ai_assistant_generates_and_serves_cached_chat(tmp_path: Path) -> None:
    generator = AiAssistantModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, tmp_path, renderer, context)
    module_dir = (
        tmp_path
        / ".rapidkit/vendor"
        / str(context["rapidkit_vendor_module"])
        / str(context["rapidkit_vendor_version"])
        / "src/modules/free/ai/ai_assistant"
    )
    vendor = _load_package_module("integration_ai_assistant_vendor", module_dir, "ai_assistant.py")

    assistant = vendor.AiAssistant()
    first = assistant.chat("Create a release checklist")
    second = assistant.chat("Add checksum validation")
    health = assistant.health_report()
    history = assistant.get_history()

    assert first.provider == "echo"
    assert first.cached is False
    assert second.cached is False
    assert "Add checksum validation" in second.content
    assert [message.role for message in history] == ["user", "assistant", "user", "assistant"]
    assert health["status"] == "ok"
    assert health["cache_entries"] == 2
