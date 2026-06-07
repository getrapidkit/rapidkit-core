def test_forms_engine_framework_adapters_are_discoverable() -> None:
    from modules.free.business.forms_engine.frameworks import list_available_plugins

    plugins = list_available_plugins()

    assert "fastapi" in plugins
    assert "nestjs" in plugins
