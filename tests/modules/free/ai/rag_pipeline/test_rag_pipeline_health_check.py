def test_rag_pipeline_health_reports_document_and_chunk_stats(rendered_rag_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_rag_pipeline["vendor"]
    pipeline = vendor.RagPipeline()
    pipeline.ingest(id="doc", text="Enterprise RAG needs citations.", namespace="tenant-a")

    health = pipeline.health()

    assert health["module"] == "rag_pipeline"
    assert health["status"] == "ok"
    assert health["stats"]["documents"] == 1
    assert health["stats"]["chunks"] == 1
    assert health["stats"]["namespaces"] == {"tenant-a": 1}
    assert health["stats"]["audit_events"] >= 1
