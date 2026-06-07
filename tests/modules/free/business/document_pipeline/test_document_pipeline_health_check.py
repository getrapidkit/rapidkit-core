def test_document_pipeline_health_check(rendered_document_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_document_pipeline["vendor"]
    runtime = vendor.DocumentPipeline()

    assert runtime.health_check()["module"] == "document_pipeline"
