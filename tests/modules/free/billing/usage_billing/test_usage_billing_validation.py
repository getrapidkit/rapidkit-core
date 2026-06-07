import pytest


def test_usage_billing_rejects_disabled_runtime(rendered_usage_billing) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_usage_billing["vendor"]
    runtime = vendor.UsageBilling(vendor.UsageBillingConfig(enabled=False))

    with pytest.raises(vendor.UsageBillingError, match="disabled"):
        runtime.register_meter(key="tokens", unit="token")


def test_usage_billing_requires_account_id(rendered_usage_billing) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_usage_billing["vendor"]
    runtime = vendor.UsageBilling()
    runtime.register_meter(key="tokens", unit="token")

    with pytest.raises(vendor.UsageBillingError, match="account_id"):
        runtime.record_usage(account_id=" ", meter="tokens", quantity=1)
