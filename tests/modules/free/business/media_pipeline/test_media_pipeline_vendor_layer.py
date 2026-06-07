def test_media_pipeline_vendor_exports_contract(rendered_media_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_media_pipeline["vendor"]

    for name in (
        "MediaPipeline",
        "MediaPipelineConfig",
        "MediaPipelineError",
        "MediaSource",
        "MediaStatus",
    ):
        assert hasattr(vendor, name)
