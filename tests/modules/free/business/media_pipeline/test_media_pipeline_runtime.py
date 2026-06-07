def test_media_pipeline_generates_variants(rendered_media_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_media_pipeline["vendor"]
    pipeline = vendor.MediaPipeline()
    source = vendor.MediaSource("hero.png", b"image-bytes", "image/png", tenant_id="tenant-a")

    asset = pipeline.ingest_and_process(source)

    assert asset.status == vendor.MediaStatus.PROCESSED
    assert [variant.name for variant in asset.variants] == ["thumbnail", "preview"]
    assert pipeline.list_assets(tenant_id="tenant-a")[0].checksum == asset.checksum
