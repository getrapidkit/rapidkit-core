def test_webhook_platform_generated_runtime_is_usable(rendered_webhook_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_webhook_platform["vendor"]

    runtime = vendor.WebhookPlatform()
    endpoint = runtime.register_endpoint(url="https://example.com/hooks", secret="secret")

    assert endpoint.id
    assert runtime.stats()["endpoints"] == 1
