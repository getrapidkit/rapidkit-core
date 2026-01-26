from pathlib import Path


def test_ai_assistant_configuration_file_exists() -> None:
    cfg = Path("src/modules/free/ai/ai_assistant/config/base.yaml")
    assert cfg.exists()
    text = cfg.read_text(encoding="utf-8")
    assert "" in text
