def test_webhook_platform_health_reports_delivery_stats(rendered_webhook_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_webhook_platform["vendor"]
    runtime = vendor.WebhookPlatform()
    runtime.register_endpoint(url="https://example.com/hooks", secret="secret")
    runtime.publish(event_type="x", payload={})

    health = runtime.health()

    assert health["module"] == "webhook_platform"
    assert health["status"] == "ok"
    assert health["stats"]["endpoints"] == 1
    assert health["stats"]["deliveries"] == 1
    assert health["stats"]["audit_events"] >= 3
