def test_usage_billing_generated_runtime_is_usable(rendered_usage_billing) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_usage_billing["vendor"]

    runtime = vendor.UsageBilling()
    meter = runtime.register_meter(key="api", unit="call")

    assert meter.key == "api"
    assert runtime.stats()["meters"] == 1
