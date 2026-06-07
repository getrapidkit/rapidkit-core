def test_audit_policy_records_append_only_hash_chain(rendered_audit_policy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_audit_policy["vendor"]
    runtime = vendor.AuditPolicy()

    first = runtime.record(
        action="product.publish",
        actor_id="admin",
        role="admin",
        resource="product:one",
        reason="ready for release",
        tenant_id="tenant-a",
    )
    second = runtime.record(
        action="product.archive",
        actor_id="admin",
        role="admin",
        resource="product:one",
        reason="deprecated",
        tenant_id="tenant-a",
    )

    assert first.previous_hash == ""
    assert second.previous_hash == first.event_hash
    assert runtime.verify_chain() is True
    assert runtime.list_events(tenant_id="tenant-a") == (first, second)


def test_audit_policy_filters_events(rendered_audit_policy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_audit_policy["vendor"]
    runtime = vendor.AuditPolicy()
    runtime.record(action="one", actor_id="a", resource="r", reason="because")
    runtime.record(action="two", actor_id="b", resource="r", reason="because")

    assert [event.action for event in runtime.list_events(actor_id="a")] == ["one"]
