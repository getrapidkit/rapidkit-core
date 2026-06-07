import pytest


def test_org_admin_console_validates_required_input(rendered_org_admin_console) -> None:
    vendor = rendered_org_admin_console["vendor"]
    console = vendor.OrgAdminConsole()

    with pytest.raises(vendor.OrgAdminConsoleError, match="required"):
        console.create_org(name="", slug="", owner_user_id="owner")
