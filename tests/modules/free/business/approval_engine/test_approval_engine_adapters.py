def test_approval_engine_exposes_runtime_contract(rendered_approval_engine) -> None:
    vendor = rendered_approval_engine["vendor"]

    assert hasattr(vendor, "ApprovalEngine")
    assert hasattr(vendor, "ApprovalPolicy")
    assert hasattr(vendor, "ApprovalStatus")
