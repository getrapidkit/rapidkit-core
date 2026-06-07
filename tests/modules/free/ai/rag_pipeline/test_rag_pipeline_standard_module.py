def test_rag_pipeline_generated_runtime_is_usable(rendered_rag_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_rag_pipeline["vendor"]

    pipeline = vendor.RagPipeline()
    document = pipeline.ingest(id="doc", text="RAG returns citations.")

    assert document.id == "doc"
    assert pipeline.stats()["documents"] == 1
    assert pipeline.answer("What does RAG return?").citations
