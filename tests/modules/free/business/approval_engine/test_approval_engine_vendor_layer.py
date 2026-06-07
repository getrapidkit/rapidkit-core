def test_approval_engine_vendor_runtime_is_generated(rendered_approval_engine) -> None:
    root = rendered_approval_engine["root"]

    assert (
        root / ".rapidkit/vendor/approval_engine/0.1.3/src/business/approval_engine.py"
    ).exists()
