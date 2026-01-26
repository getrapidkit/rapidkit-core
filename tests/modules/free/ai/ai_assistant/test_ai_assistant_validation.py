from modules.free.ai.ai_assistant import generate


def test_ai_assistant_validation_basic() -> None:
    cfg = generate.load_module_config()
    assert "name" in cfg and cfg.get("name") == "ai_assistant"
