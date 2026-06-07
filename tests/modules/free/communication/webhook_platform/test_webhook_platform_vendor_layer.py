def test_webhook_platform_vendor_exports_runtime_contract(rendered_webhook_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_webhook_platform["vendor"]

    for name in (
        "WebhookPlatform",
        "WebhookPlatformConfig",
        "WebhookPlatformError",
        "WebhookEndpoint",
        "WebhookEvent",
        "WebhookDelivery",
        "sign_payload",
        "verify_signature",
    ):
        assert hasattr(vendor, name)
