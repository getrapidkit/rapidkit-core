def test_event_bus_framework_adapters_are_discoverable() -> None:
    from modules.free.tasks.event_bus.frameworks import list_available_plugins

    plugins = list_available_plugins()
    assert "fastapi" in plugins
    assert "nestjs" in plugins
