def test_audit_policy_health_reports_chain_stats(rendered_audit_policy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_audit_policy["vendor"]
    runtime = vendor.AuditPolicy()
    runtime.record(action="publish", actor_id="admin", resource="product:1", reason="ready")

    health = runtime.health()

    assert health["module"] == "audit_policy"
    assert health["status"] == "ok"
    assert health["stats"]["events"] == 1
    assert health["stats"]["chain_valid"] is True
