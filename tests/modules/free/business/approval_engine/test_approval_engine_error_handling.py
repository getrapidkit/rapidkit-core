import pytest


def test_approval_engine_rejects_missing_policy(rendered_approval_engine) -> None:
    vendor = rendered_approval_engine["vendor"]
    engine = vendor.ApprovalEngine()

    with pytest.raises(vendor.ApprovalEngineError, match="policy not found"):
        engine.request_approval(
            policy_key="missing",
            action="publish",
            requester_id="admin",
            reason="release",
        )
