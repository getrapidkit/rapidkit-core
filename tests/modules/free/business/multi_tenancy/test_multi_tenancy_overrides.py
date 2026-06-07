from modules.free.business.multi_tenancy.overrides import MultiTenancyOverrides


def test_multi_tenancy_overrides_are_configurable() -> None:
    overrides = MultiTenancyOverrides()

    assert overrides.get_override_info() == {"method_overrides": [], "setting_overrides": []}
    assert hasattr(overrides, "call_original")
