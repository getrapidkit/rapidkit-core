from modules.free.business.org_admin_console import overrides


def test_org_admin_console_overrides_contract_loads() -> None:
    assert hasattr(overrides, "OrgAdminConsoleOverrides")
