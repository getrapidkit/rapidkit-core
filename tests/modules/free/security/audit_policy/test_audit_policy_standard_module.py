def test_audit_policy_generated_runtime_is_usable(rendered_audit_policy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_audit_policy["vendor"]

    runtime = vendor.AuditPolicy()
    event = runtime.record(action="x", actor_id="a", resource="r", reason="needed")

    assert event.event_hash
    assert runtime.stats()["events"] == 1
