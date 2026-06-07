import pytest


def test_document_pipeline_rejects_unsupported_extension(rendered_document_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_document_pipeline["vendor"]
    pipeline = vendor.DocumentPipeline()

    with pytest.raises(vendor.DocumentPipelineError):
        pipeline.ingest(vendor.DocumentSource(filename="malware.exe", content=b"x"))
