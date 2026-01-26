from modules.free.ai.ai_assistant import generate


def test_ai_assistant_versioning_smoke() -> None:
    cfg = generate.load_module_config()
    assert "version" in cfg
