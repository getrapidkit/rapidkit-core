import pytest


def test_admin_console_validates_required_input(rendered_admin_console) -> None:
    vendor = rendered_admin_console["vendor"]
    with pytest.raises(vendor.AdminConsoleError, match="key"):
        vendor.AdminConsole().register_action(
            vendor.AdminAction(key="", label="Bad", required_roles=("admin",))
        )
