import pytest


def test_usage_billing_rejects_unknown_meter(rendered_usage_billing) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_usage_billing["vendor"]
    runtime = vendor.UsageBilling()

    with pytest.raises(vendor.UsageBillingError, match="meter not found"):
        runtime.record_usage(account_id="acct_1", meter="missing", quantity=1)


def test_usage_billing_rejects_negative_quantity(rendered_usage_billing) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_usage_billing["vendor"]
    runtime = vendor.UsageBilling()
    runtime.register_meter(key="tokens", unit="token")

    with pytest.raises(vendor.UsageBillingError, match="non-negative"):
        runtime.record_usage(account_id="acct_1", meter="tokens", quantity=-1)
