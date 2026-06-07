import pytest


def test_webhook_platform_rejects_disabled_runtime(rendered_webhook_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_webhook_platform["vendor"]
    runtime = vendor.WebhookPlatform(vendor.WebhookPlatformConfig(enabled=False))

    with pytest.raises(vendor.WebhookPlatformError, match="disabled"):
        runtime.register_endpoint(url="https://example.com", secret="secret")


def test_webhook_platform_requires_event_type(rendered_webhook_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_webhook_platform["vendor"]
    runtime = vendor.WebhookPlatform()

    with pytest.raises(vendor.WebhookPlatformError, match="event_type"):
        runtime.publish(event_type=" ", payload={})
