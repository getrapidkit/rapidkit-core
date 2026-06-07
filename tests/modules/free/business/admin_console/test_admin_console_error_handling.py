import pytest


def test_admin_console_raises_domain_error_for_missing_resource(rendered_admin_console) -> None:
    vendor = rendered_admin_console["vendor"]
    console = vendor.AdminConsole()

    with pytest.raises(vendor.AdminConsoleError, match="not found"):
        console.run_action("missing", actor_id="admin-1", actor_role="admin", reason="audit")
