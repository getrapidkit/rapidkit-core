def test_usage_billing_vendor_exports_runtime_contract(rendered_usage_billing) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_usage_billing["vendor"]

    for name in (
        "UsageBilling",
        "UsageBillingConfig",
        "UsageBillingError",
        "UsageMeter",
        "UsageEvent",
        "UsageSummary",
        "QuotaDecision",
    ):
        assert hasattr(vendor, name)
