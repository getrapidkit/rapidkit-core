def test_document_pipeline_config_defaults(rendered_document_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_document_pipeline["vendor"]
    config = vendor.DocumentPipelineConfig()

    assert config.enabled is True
