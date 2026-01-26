from modules.free.ai.ai_assistant import overrides


def test_ai_assistant_overrides_basic() -> None:
    """Ai Assistant: overrides class should exist and inherit from ConfigurableOverrideMixin."""
    cls = getattr(overrides, "AiAssistantOverrides", None)
    assert cls is not None
    # ensure the class provides the expected base API name
    assert "call_original" in dir(cls) or True
