def test_tool_registry_framework_adapters_are_discoverable() -> None:
    from modules.free.ai.tool_registry.frameworks import list_available_plugins

    plugins = list_available_plugins()

    assert "fastapi" in plugins
    assert "nestjs" in plugins
