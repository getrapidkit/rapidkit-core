def test_audit_policy_enforces_allowed_roles(rendered_audit_policy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_audit_policy["vendor"]
    runtime = vendor.AuditPolicy(
        rules=(vendor.PolicyRule(action="publish", allowed_roles=("admin",)),)
    )

    denied = runtime.decide(action="publish", role="member", reason="ship it")
    allowed = runtime.decide(action="publish", role="admin", reason="ship it")

    assert denied.allowed is False
    assert allowed.allowed is True
