import pytest


def test_rag_pipeline_rejects_disabled_runtime(rendered_rag_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_rag_pipeline["vendor"]
    pipeline = vendor.RagPipeline(vendor.RagPipelineConfig(enabled=False))

    with pytest.raises(vendor.RagPipelineError, match="disabled"):
        pipeline.ingest(text="disabled")


def test_rag_pipeline_rejects_invalid_chunk_settings(rendered_rag_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_rag_pipeline["vendor"]

    with pytest.raises(vendor.RagPipelineError, match="chunk_overlap"):
        vendor.RagPipeline(vendor.RagPipelineConfig(chunk_size=10, chunk_overlap=10))
