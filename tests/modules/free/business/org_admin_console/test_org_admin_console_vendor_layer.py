def test_org_admin_console_vendor_runtime_is_generated(rendered_org_admin_console) -> None:
    root = rendered_org_admin_console["root"]

    assert (
        root / ".rapidkit/vendor/org_admin_console/0.1.3/src/business/org_admin_console.py"
    ).exists()
