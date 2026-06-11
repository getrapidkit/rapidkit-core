def test_approval_engine_vendor_runtime_is_generated(rendered_approval_engine) -> None:
    root = rendered_approval_engine["root"]
    config = rendered_approval_engine["config"]

    assert (
        root
        / ".rapidkit"
        / "vendor"
        / config["name"]
        / config["version"]
        / "src/modules/free/business/approval_engine/approval_engine.py"
    ).exists()
