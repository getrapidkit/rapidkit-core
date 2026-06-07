def test_document_pipeline_vendor_exports_contract(rendered_document_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_document_pipeline["vendor"]

    for name in (
        "DocumentPipeline",
        "DocumentPipelineConfig",
        "DocumentPipelineError",
        "DocumentSource",
        "DocumentRecord",
        "DocumentChunk",
        "DocumentStatus",
    ):
        assert hasattr(vendor, name)
