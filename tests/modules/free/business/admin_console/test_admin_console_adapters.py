def test_admin_console_exposes_runtime_contract(rendered_admin_console) -> None:
    vendor = rendered_admin_console["vendor"]

    assert hasattr(vendor, "AdminConsole")
    assert hasattr(vendor, "AdminAction")
    assert hasattr(vendor, "AdminActionRun")
