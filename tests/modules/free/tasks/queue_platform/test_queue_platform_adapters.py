def test_queue_platform_framework_adapters_are_discoverable() -> None:
    from modules.free.tasks.queue_platform.frameworks import list_available_plugins

    plugins = list_available_plugins()

    assert "fastapi" in plugins
    assert "nestjs" in plugins
