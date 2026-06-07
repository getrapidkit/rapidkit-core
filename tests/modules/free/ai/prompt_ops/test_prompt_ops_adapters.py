def test_prompt_ops_framework_adapters_are_discoverable() -> None:
    from modules.free.ai.prompt_ops.frameworks import list_available_plugins

    plugins = list_available_plugins()

    assert "fastapi" in plugins
    assert "nestjs" in plugins
