import pytest


def test_approval_engine_policy_validation(rendered_approval_engine) -> None:
    vendor = rendered_approval_engine["vendor"]
    engine = vendor.ApprovalEngine()

    with pytest.raises(vendor.ApprovalEngineError, match="policy key"):
        engine.register_policy(key="")
