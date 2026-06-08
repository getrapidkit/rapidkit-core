def test_support_center_vendor_runtime_is_generated(rendered_support_center) -> None:
    root = rendered_support_center["root"]
    config = rendered_support_center["config"]

    assert (
        root
        / ".rapidkit"
        / "vendor"
        / config["name"]
        / config["version"]
        / "src/modules/free/business/support_center/support_center.py"
    ).exists()
