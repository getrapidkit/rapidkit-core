def test_queue_platform_generated_runtime_is_usable(rendered_queue_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_queue_platform["vendor"]
    runtime = vendor.QueuePlatform()

    assert runtime.health_check()["enabled"] is True
