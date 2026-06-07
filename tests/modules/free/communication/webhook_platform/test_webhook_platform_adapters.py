def test_webhook_platform_filters_by_tenant_and_event(rendered_webhook_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_webhook_platform["vendor"]
    runtime = vendor.WebhookPlatform()
    runtime.register_endpoint(
        url="https://example.com/a",
        secret="secret",
        events=("order.created",),
        tenant_id="tenant-a",
    )
    runtime.register_endpoint(url="https://example.com/b", secret="secret", events=("other",))

    event = runtime.publish(
        event_type="order.created",
        payload={},
        tenant_id="tenant-a",
    )

    assert len(runtime.list_deliveries(event_id=event.id)) == 1
