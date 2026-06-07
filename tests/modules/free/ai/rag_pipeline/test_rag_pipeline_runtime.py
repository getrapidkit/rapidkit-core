def test_rag_pipeline_ingests_retrieves_and_answers(rendered_rag_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_rag_pipeline["vendor"]
    pipeline = vendor.RagPipeline()

    pipeline.ingest(
        id="rapidkit",
        text="RapidKit workspaces compose FastAPI and NestJS product modules.",
        metadata={"tenant_id": "acme", "kind": "docs"},
    )

    citations = pipeline.retrieve("What does RapidKit compose?", metadata_filter={"kind": "docs"})
    answer = pipeline.answer("What does RapidKit compose?")

    assert citations[0].document_id == "rapidkit"
    assert "RapidKit workspaces" in answer.answer
    assert answer.metadata["citation_count"] == 1
    assert len(pipeline.audit_events(event_type="answer.generated")) == 1


def test_rag_pipeline_filters_by_namespace_and_metadata(rendered_rag_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_rag_pipeline["vendor"]
    pipeline = vendor.RagPipeline()

    pipeline.ingest(id="public", text="Public documentation", metadata={"tier": "free"})
    pipeline.ingest(
        id="private",
        text="Private launch checklist",
        namespace="tenant-a",
        metadata={"tier": "pro"},
    )

    results = pipeline.retrieve(
        "launch checklist",
        namespace="tenant-a",
        metadata_filter={"tier": "pro"},
    )

    assert [citation.document_id for citation in results] == ["private"]
    assert pipeline.retrieve("launch checklist", metadata_filter={"tier": "pro"}) == ()


def test_rag_pipeline_tenant_filter_and_idempotency(rendered_rag_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_rag_pipeline["vendor"]
    pipeline = vendor.RagPipeline()

    first = pipeline.ingest(
        id="tenant-doc",
        text="Tenant A private doc",
        namespace="tenant-a",
        metadata={"tenant_id": "tenant-a"},
        idempotency_key="tenant-doc-v1",
    )
    second = pipeline.ingest(
        id="ignored",
        text="Ignored",
        namespace="tenant-a",
        metadata={"tenant_id": "tenant-a"},
        idempotency_key="tenant-doc-v1",
    )

    assert second.id == first.id
    assert pipeline.retrieve("private", namespace="tenant-a", tenant_id="tenant-a")
    assert pipeline.retrieve("private", namespace="tenant-a", tenant_id="tenant-b") == ()
