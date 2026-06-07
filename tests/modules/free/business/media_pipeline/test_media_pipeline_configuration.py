def test_media_pipeline_config_defaults(rendered_media_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_media_pipeline["vendor"]
    config = vendor.MediaPipelineConfig()

    assert config.enabled is True
