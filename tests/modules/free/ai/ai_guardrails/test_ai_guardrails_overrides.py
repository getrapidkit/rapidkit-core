from modules.free.ai.ai_guardrails import overrides


def test_ai_guardrails_overrides_module_is_importable() -> None:
    assert overrides is not None
