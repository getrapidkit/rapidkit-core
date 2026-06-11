def test_admin_console_vendor_runtime_is_generated(rendered_admin_console) -> None:
    root = rendered_admin_console["root"]
    config = rendered_admin_console["config"]

    assert (
        root
        / ".rapidkit"
        / "vendor"
        / config["name"]
        / config["version"]
        / "src/modules/free/business/admin_console/admin_console.py"
    ).exists()
