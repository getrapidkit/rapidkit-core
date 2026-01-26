from __future__ import annotations

from pathlib import Path

from modules.free.ai.ai_assistant.scripts import run_demo


def test_quickstart_demo_generates_fastapi_variant(monkeypatch, tmp_path: Path) -> None:
    demo_root = tmp_path / "demo"

    def _fake_mkdtemp(prefix: str) -> str:
        demo_root.mkdir(parents=True, exist_ok=True)
        return str(demo_root)

    monkeypatch.setattr(run_demo.tempfile, "mkdtemp", _fake_mkdtemp)

    exit_code = run_demo.main([])
    assert exit_code == 0

    expected_vendor = (
        demo_root / "src" / "modules" / "free" / "ai" / "ai_assistant" / "ai_assistant.py"
    )
    expected_router = (
        demo_root
        / "src"
        / "modules"
        / "free"
        / "ai"
        / "ai_assistant"
        / "routers"
        / "ai"
        / "ai_assistant.py"
    )
    assert expected_vendor.exists()
    assert expected_router.exists()
