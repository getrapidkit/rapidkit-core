def test_audit_policy_vendor_exports_runtime_contract(rendered_audit_policy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_audit_policy["vendor"]

    for name in (
        "AuditPolicy",
        "AuditPolicyConfig",
        "AuditPolicyError",
        "AuditEvent",
        "PolicyRule",
        "PolicyDecision",
    ):
        assert hasattr(vendor, name)
