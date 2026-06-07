from __future__ import annotations

import pytest


def test_approval_engine_requires_reasons_and_authorized_reviewer(rendered_approval_engine) -> None:
    vendor = rendered_approval_engine["vendor"]
    engine = vendor.ApprovalEngine()
    engine.register_policy(key="commerce.publish", required_roles=("publisher",))

    with pytest.raises(vendor.ApprovalEngineError, match="reason is required"):
        engine.request_approval(
            policy_key="commerce.publish",
            action="publish product",
            requester_id="admin-1",
            reason="",
        )

    request = engine.request_approval(
        policy_key="commerce.publish",
        action="publish product",
        requester_id="admin-1",
        reason="readiness score passed",
        tenant_id="tenant-1",
    )

    with pytest.raises(vendor.ApprovalEngineError, match="reviewer role is not allowed"):
        engine.decide(
            request.id,
            reviewer_id="reviewer-1",
            reviewer_role="support",
            approved=True,
            reason="wrong role",
        )

    approved = engine.decide(
        request.id,
        reviewer_id="reviewer-2",
        reviewer_role="publisher",
        approved=True,
        reason="release gate passed",
    )

    assert approved.status == vendor.ApprovalStatus.APPROVED
    assert approved.decision_reason == "release gate passed"
    assert [event.type for event in engine.audit_events(request_id=request.id)] == [
        "approval.requested",
        "approval.approved",
    ]


def test_approval_engine_escalates_pending_requests(rendered_approval_engine) -> None:
    vendor = rendered_approval_engine["vendor"]
    engine = vendor.ApprovalEngine()
    engine.register_policy(key="backup.import", required_roles=("ops",), escalation_role="owner")
    request = engine.request_approval(
        policy_key="backup.import",
        action="import backup",
        requester_id="ops-1",
        reason="customer recovery",
    )

    escalated = engine.escalate(request.id, actor_id="ops-lead", reason="needs owner review")

    assert escalated.status == vendor.ApprovalStatus.ESCALATED
    assert engine.health()["requests"] == 1
    assert engine.audit_events(request_id=request.id)[-1].type == "approval.escalated"
