def test_ai_guardrails_framework_adapters_are_discoverable() -> None:
    from modules.free.ai.ai_guardrails.frameworks import list_available_plugins

    plugins = list_available_plugins()

    assert "fastapi" in plugins
    assert "nestjs" in plugins
