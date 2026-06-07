from modules.free.business.support_center import overrides


def test_support_center_overrides_contract_loads() -> None:
    assert hasattr(overrides, "SupportCenterOverrides")
