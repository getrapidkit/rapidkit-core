from pathlib import Path


def test_ai_assistant_vendor_snapshot_exists() -> None:
    base = Path("src/modules/free/ai/ai_assistant")
    assert (base / "module.verify.json").exists()
    assert (base / "templates" / "base" / "ai_assistant.py.j2").exists()
