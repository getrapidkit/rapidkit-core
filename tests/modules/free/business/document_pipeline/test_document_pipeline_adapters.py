def test_document_pipeline_framework_adapters_are_discoverable() -> None:
    from modules.free.business.document_pipeline.frameworks import list_available_plugins

    plugins = list_available_plugins()
    assert "fastapi" in plugins
    assert "nestjs" in plugins
