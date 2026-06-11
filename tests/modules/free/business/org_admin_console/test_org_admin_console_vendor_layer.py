def test_org_admin_console_vendor_runtime_is_generated(rendered_org_admin_console) -> None:
    root = rendered_org_admin_console["root"]
    config = rendered_org_admin_console["config"]

    assert (
        root
        / ".rapidkit"
        / "vendor"
        / config["name"]
        / config["version"]
        / "src/modules/free/business/org_admin_console/org_admin_console.py"
    ).exists()
