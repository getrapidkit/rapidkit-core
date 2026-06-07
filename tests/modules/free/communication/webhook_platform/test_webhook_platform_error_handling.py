import pytest


def test_webhook_platform_rejects_invalid_endpoint_url(rendered_webhook_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_webhook_platform["vendor"]
    runtime = vendor.WebhookPlatform()

    with pytest.raises(vendor.WebhookPlatformError, match="http"):
        runtime.register_endpoint(url="ftp://example.com", secret="secret")


def test_webhook_platform_retries_failed_deliveries(rendered_webhook_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_webhook_platform["vendor"]
    responses = [500, 200]

    def handler(_url, _headers, _payload):  # type: ignore[no-untyped-def]
        return responses.pop(0), "response"

    runtime = vendor.WebhookPlatform(handler=handler)
    runtime.register_endpoint(url="https://example.com/hooks", secret="secret")
    runtime.publish(event_type="x", payload={})

    retry = runtime.retry_failed()

    assert retry[0].attempt == 2
    assert retry[0].status == "delivered"


def test_webhook_platform_enforces_tenant_scope_on_dispatch(rendered_webhook_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_webhook_platform["vendor"]
    runtime = vendor.WebhookPlatform()
    runtime.register_endpoint(
        url="https://example.com/hooks", secret="secret", tenant_id="tenant-a"
    )
    event = runtime.publish(event_type="x", payload={}, tenant_id="tenant-a")

    with pytest.raises(vendor.WebhookPlatformError, match="tenant"):
        runtime.dispatch(event.id, tenant_id="tenant-b")
