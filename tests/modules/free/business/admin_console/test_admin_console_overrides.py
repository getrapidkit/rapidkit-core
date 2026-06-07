from modules.free.business.admin_console import overrides


def test_admin_console_overrides_contract_loads() -> None:
    assert hasattr(overrides, "AdminConsoleOverrides")
