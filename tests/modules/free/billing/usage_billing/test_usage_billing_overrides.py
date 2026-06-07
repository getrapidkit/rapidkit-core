from modules.free.billing.usage_billing.overrides import UsageBillingOverrides


def test_usage_billing_overrides_are_configurable() -> None:
    overrides = UsageBillingOverrides()

    assert overrides.get_override_info() == {"method_overrides": [], "setting_overrides": []}
    assert hasattr(overrides, "call_original")
