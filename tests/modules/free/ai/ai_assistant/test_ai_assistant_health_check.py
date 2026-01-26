from __future__ import annotations

import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Iterator, Mapping
from uuid import uuid4

from modules.free.ai.ai_assistant import generate
from modules.shared.generator import TemplateRenderer


def test_ai_assistant_health_template_present() -> None:
    # Ensure vendor and variant health templates are present
    base = Path("src/modules/free/ai/ai_assistant/templates")
    assert (base / "base" / "ai_assistant_health.py.j2").exists()
    assert (base / "variants" / "fastapi" / "ai_assistant_health.py.j2").exists()


@contextmanager
def _runtime_stub() -> Iterator[str]:
    stub_name = f"ai_assistant_runtime_stub_{uuid4().hex}"
    stub_module = ModuleType(stub_name)

    class _StubConfig:
        def __init__(self, region: str = "us-east-1", *, retries: int = 1) -> None:
            self.region = region
            self.retries = retries

    class _StubAssistant:
        def __init__(self, cfg: _StubConfig | None = None) -> None:
            self.config = cfg or _StubConfig()

        def health_report(self) -> Mapping[str, object]:
            return {
                "status": "ok",
                "metadata": {
                    "region": self.config.region,
                    "retries": self.config.retries,
                },
            }

    stub_module.AiAssistantConfig = _StubConfig  # type: ignore[attr-defined]
    stub_module.AiAssistant = _StubAssistant  # type: ignore[attr-defined]
    sys.modules[stub_name] = stub_module
    try:
        yield stub_name
    finally:
        sys.modules.pop(stub_name, None)


def _load_health_module(tmp_path: Path) -> tuple[object, str]:
    renderer = TemplateRenderer(generate.MODULE_ROOT / "templates")
    config = generate.load_module_config()
    context = generate.build_base_context(config)
    health_py = tmp_path / f"ai_assistant_health_{uuid4().hex}.py"
    health_py.write_text(
        renderer.render_template("base/ai_assistant_health.py.j2", context),
        encoding="utf-8",
    )

    module_name = f"ai_assistant_health_module_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, health_py)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader  # narrow types for mypy/pyright
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module, module_name


def test_ai_assistant_health_template_executes(tmp_path: Path) -> None:
    with _runtime_stub():
        module, module_name = _load_health_module(tmp_path)
        try:
            payload = module.check_health(context={"request_id": "req-123"})
        finally:
            sys.modules.pop(module_name, None)

    assert payload["status"] == "ok"
    assert payload["metadata"]["region"] == "us-east-1"
    assert payload["metadata"]["request_id"] == "req-123"
