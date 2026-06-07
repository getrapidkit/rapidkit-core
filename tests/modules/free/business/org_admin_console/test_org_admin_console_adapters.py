def test_org_admin_console_exposes_runtime_contract(rendered_org_admin_console) -> None:
    vendor = rendered_org_admin_console["vendor"]

    assert hasattr(vendor, "OrgAdminConsole")
    assert hasattr(vendor, "Organization")
    assert hasattr(vendor, "OrgMember")
    assert hasattr(vendor, "OrgInvitation")
