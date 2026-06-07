import pytest


def test_org_admin_console_raises_domain_error_for_missing_resource(
    rendered_org_admin_console,
) -> None:
    vendor = rendered_org_admin_console["vendor"]
    console = vendor.OrgAdminConsole()

    with pytest.raises(vendor.OrgAdminConsoleError, match="organization not found"):
        console.invite_member(
            org_id="missing", email="admin@example.com", role="admin", actor_id="owner"
        )
