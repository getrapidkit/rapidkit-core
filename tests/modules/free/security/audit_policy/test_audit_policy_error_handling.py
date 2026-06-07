import pytest


def test_audit_policy_requires_reason_by_default(rendered_audit_policy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_audit_policy["vendor"]
    runtime = vendor.AuditPolicy()

    with pytest.raises(vendor.AuditPolicyError, match="reason"):
        runtime.record(action="backup.import", actor_id="admin", resource="backup:1", reason="")


def test_audit_policy_rejects_empty_actor(rendered_audit_policy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_audit_policy["vendor"]
    runtime = vendor.AuditPolicy()

    with pytest.raises(vendor.AuditPolicyError, match="actor_id"):
        runtime.record(action="x", actor_id=" ", resource="resource", reason="ok")
