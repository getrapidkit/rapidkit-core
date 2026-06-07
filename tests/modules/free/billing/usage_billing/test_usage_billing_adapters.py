def test_usage_billing_lists_events_by_account_and_meter(rendered_usage_billing) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_usage_billing["vendor"]
    runtime = vendor.UsageBilling()
    runtime.register_meter(key="tokens", unit="token")
    runtime.register_meter(key="seats", unit="seat")
    runtime.record_usage(account_id="acct_1", meter="tokens", quantity=10)
    runtime.record_usage(account_id="acct_2", meter="seats", quantity=2)

    assert len(runtime.list_events(account_id="acct_1")) == 1
    assert len(runtime.list_events(meter="seats")) == 1
