from decimal import Decimal


def test_usage_billing_records_idempotent_usage_and_summary(rendered_usage_billing) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_usage_billing["vendor"]
    runtime = vendor.UsageBilling()
    runtime.register_meter(
        key="api_calls",
        unit="call",
        price_per_unit="0.10",
        included_units=100,
    )

    first = runtime.record_usage(
        account_id="acct_1",
        meter="api_calls",
        quantity=125,
        idempotency_key="evt_1",
    )
    second = runtime.record_usage(
        account_id="acct_1",
        meter="api_calls",
        quantity=999,
        idempotency_key="evt_1",
    )
    summary = runtime.summarize(account_id="acct_1", meter="api_calls")

    assert first == second
    assert summary.quantity == Decimal("125")
    assert summary.billable_units == Decimal("25")
    assert summary.estimated_amount == Decimal("2.50")
    assert runtime.stats()["audit_events"] >= 3


def test_usage_billing_enforces_hard_limit(rendered_usage_billing) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_usage_billing["vendor"]
    runtime = vendor.UsageBilling()
    runtime.register_meter(key="tokens", unit="token", hard_limit=1000)
    runtime.record_usage(account_id="acct_1", meter="tokens", quantity=900)

    decision = runtime.check_quota(account_id="acct_1", meter="tokens", quantity=101)

    assert decision.allowed is False
    assert decision.reason == "hard limit exceeded"


def test_usage_billing_closes_billing_cycle_with_receipt(rendered_usage_billing) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_usage_billing["vendor"]
    runtime = vendor.UsageBilling()
    runtime.register_meter(key="tokens", unit="token", price_per_unit="0.01", included_units=10)
    runtime.record_usage(
        account_id="acct_1",
        meter="tokens",
        quantity=35,
        tenant_id="tenant-a",
    )

    receipt = runtime.close_billing_cycle(account_id="acct_1", meter="tokens", tenant_id="tenant-a")

    assert receipt["meter"] == "tokens"
    assert receipt["estimated_amount"] == "0.25"
    assert runtime.audit_events(account_id="acct_1", tenant_id="tenant-a")
