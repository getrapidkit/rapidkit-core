import pytest


def test_rag_pipeline_rejects_empty_documents(rendered_rag_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_rag_pipeline["vendor"]
    pipeline = vendor.RagPipeline()

    with pytest.raises(vendor.RagPipelineError, match="text"):
        pipeline.ingest(text="   ")


def test_rag_pipeline_rejects_invalid_top_k(rendered_rag_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_rag_pipeline["vendor"]
    pipeline = vendor.RagPipeline(vendor.RagPipelineConfig(max_top_k=2))

    with pytest.raises(vendor.RagPipelineError, match="top_k"):
        pipeline.retrieve("question", top_k=3)
