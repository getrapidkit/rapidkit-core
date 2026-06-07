def test_rag_pipeline_vendor_exports_runtime_contract(rendered_rag_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_rag_pipeline["vendor"]

    for name in (
        "RagPipeline",
        "RagPipelineConfig",
        "RagPipelineError",
        "RagDocument",
        "RagChunk",
        "RagCitation",
        "RagQuery",
        "RagAnswer",
        "deterministic_embed",
    ):
        assert hasattr(vendor, name)

    assert len(vendor.deterministic_embed("hello", 8)) == 8
