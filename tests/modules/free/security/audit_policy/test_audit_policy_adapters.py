def test_audit_policy_can_add_rules_after_initialization(rendered_audit_policy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_audit_policy["vendor"]
    runtime = vendor.AuditPolicy()

    runtime.add_rule(vendor.PolicyRule(action="assign.entitlement", denied_roles=("support",)))

    decision = runtime.decide(action="assign.entitlement", role="support", reason="manual grant")

    assert decision.allowed is False
    assert decision.reason == "role is denied"
