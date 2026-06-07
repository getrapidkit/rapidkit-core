def test_queue_platform_config_defaults(rendered_queue_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_queue_platform["vendor"]
    config = vendor.QueuePlatformConfig()

    assert config.enabled is True
