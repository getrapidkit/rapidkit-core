from modules.free.ai.ai_assistant import generate


def test_ai_assistant_runtime_loads_config() -> None:
    cfg = generate.load_module_config()
    assert isinstance(cfg, dict)
    assert cfg.get("name") == "ai_assistant"
