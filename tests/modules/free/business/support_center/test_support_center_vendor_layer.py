def test_support_center_vendor_runtime_is_generated(rendered_support_center) -> None:
    root = rendered_support_center["root"]

    assert (root / ".rapidkit/vendor/support_center/0.1.3/src/business/support_center.py").exists()
