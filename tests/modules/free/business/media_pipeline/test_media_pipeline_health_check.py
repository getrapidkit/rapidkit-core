def test_media_pipeline_health_check_counts_assets(rendered_media_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_media_pipeline["vendor"]
    pipeline = vendor.MediaPipeline()
    pipeline.ingest_and_process(vendor.MediaSource("hero.png", b"image", "image/png"))

    assert pipeline.health_check()["processed"] == 1
    assert pipeline.health_check()["assets"] == 1
