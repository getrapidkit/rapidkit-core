def test_document_pipeline_processes_and_chunks(rendered_document_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_document_pipeline["vendor"]
    pipeline = vendor.DocumentPipeline(
        vendor.DocumentPipelineConfig(chunk_size=10, chunk_overlap=2)
    )

    record = pipeline.ingest_and_process(
        vendor.DocumentSource(
            filename="invoice.txt", content=b"invoice payment due soon", tenant_id="t1"
        )
    )

    assert record.status == vendor.DocumentStatus.PROCESSED
    assert record.classification == "finance"
    assert len(record.chunks) >= 2
    assert pipeline.list_documents(tenant_id="t1") == [record]
