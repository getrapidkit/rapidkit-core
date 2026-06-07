def test_admin_console_vendor_runtime_is_generated(rendered_admin_console) -> None:
    root = rendered_admin_console["root"]

    assert (root / ".rapidkit/vendor/admin_console/0.1.3/src/business/admin_console.py").exists()
