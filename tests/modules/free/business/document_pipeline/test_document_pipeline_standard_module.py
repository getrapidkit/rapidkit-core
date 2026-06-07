def test_document_pipeline_generated_runtime_is_usable(rendered_document_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_document_pipeline["vendor"]
    runtime = vendor.DocumentPipeline()
    assert runtime.health_check()["enabled"] is True
