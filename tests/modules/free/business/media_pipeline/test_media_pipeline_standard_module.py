def test_media_pipeline_generated_runtime_is_usable(rendered_media_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_media_pipeline["vendor"]
    runtime = vendor.MediaPipeline()

    assert runtime.health_check()["enabled"] is True
