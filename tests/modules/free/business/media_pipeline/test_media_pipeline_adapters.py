def test_media_pipeline_framework_adapters_are_discoverable() -> None:
    from modules.free.business.media_pipeline.frameworks import list_available_plugins

    plugins = list_available_plugins()

    assert "fastapi" in plugins
    assert "nestjs" in plugins
