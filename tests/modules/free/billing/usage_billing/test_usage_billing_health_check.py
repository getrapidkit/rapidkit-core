def test_usage_billing_health_reports_metering_stats(rendered_usage_billing) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_usage_billing["vendor"]
    runtime = vendor.UsageBilling()
    runtime.register_meter(key="tokens", unit="token")
    runtime.record_usage(account_id="acct_1", meter="tokens", quantity=10)

    health = runtime.health()

    assert health["module"] == "usage_billing"
    assert health["status"] == "ok"
    assert health["stats"]["meters"] == 1
    assert health["stats"]["events"] == 1
    assert health["stats"]["accounts"] == 1
