def test_media_pipeline_rejects_disallowed_mime_type(rendered_media_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_media_pipeline["vendor"]
    pipeline = vendor.MediaPipeline()
    source = vendor.MediaSource("payload.exe", b"binary", "application/octet-stream")

    try:
        pipeline.ingest(source)
    except vendor.MediaPipelineError as exc:
        assert "not allowed" in str(exc)
    else:
        raise AssertionError("expected MediaPipelineError")


def test_media_pipeline_moderation_rejection(rendered_media_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_media_pipeline["vendor"]
    pipeline = vendor.MediaPipeline()
    source = vendor.MediaSource("hero.png", b"image", "image/png", metadata={"unsafe": True})

    asset = pipeline.ingest_and_process(source)

    assert asset.status == vendor.MediaStatus.REJECTED
    assert asset.error == "unsafe metadata flag"
