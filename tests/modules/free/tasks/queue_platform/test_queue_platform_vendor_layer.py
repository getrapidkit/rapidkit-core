def test_queue_platform_vendor_exports_contract(rendered_queue_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_queue_platform["vendor"]

    for name in (
        "QueuePlatform",
        "QueuePlatformConfig",
        "QueuePlatformError",
        "QueueMessage",
        "QueueMessageStatus",
    ):
        assert hasattr(vendor, name)
