def test_webhook_platform_delivers_matching_events_with_signature(rendered_webhook_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_webhook_platform["vendor"]
    calls = []

    def handler(url, headers, payload):  # type: ignore[no-untyped-def]
        calls.append((url, headers, payload))
        return 204, "ok"

    runtime = vendor.WebhookPlatform(handler=handler)
    endpoint = runtime.register_endpoint(
        url="https://example.com/hooks",
        secret="secret",
        events=("order.created",),
    )
    event = runtime.publish(event_type="order.created", payload={"order_id": "ord_1"})

    deliveries = runtime.list_deliveries(event_id=event.id)

    assert len(calls) == 1
    assert deliveries[0].endpoint_id == endpoint.id
    assert deliveries[0].status == "delivered"
    assert vendor.verify_signature("secret", {"order_id": "ord_1"}, deliveries[0].signature)


def test_webhook_platform_publish_is_idempotent(rendered_webhook_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_webhook_platform["vendor"]
    runtime = vendor.WebhookPlatform()
    runtime.register_endpoint(url="https://example.com/hooks", secret="secret")

    first = runtime.publish(event_type="x", payload={"n": 1}, idempotency_key="k")
    second = runtime.publish(event_type="x", payload={"n": 2}, idempotency_key="k")

    assert first == second
    assert runtime.stats()["events"] == 1


def test_webhook_platform_replays_delivery(rendered_webhook_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_webhook_platform["vendor"]
    runtime = vendor.WebhookPlatform()
    runtime.register_endpoint(url="https://example.com/hooks", secret="secret")
    event = runtime.publish(event_type="x", payload={"v": 1}, tenant_id="tenant-a")
    original = runtime.list_deliveries(event_id=event.id)[0]

    replayed = runtime.replay_delivery(original.id, tenant_id="tenant-a")

    assert replayed.attempt == original.attempt + 1
    assert replayed.event_id == original.event_id
