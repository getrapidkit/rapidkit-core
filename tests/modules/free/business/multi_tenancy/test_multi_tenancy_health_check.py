def test_multi_tenancy_health_reports_registry_stats(rendered_multi_tenancy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_multi_tenancy["vendor"]
    runtime = vendor.MultiTenancy()
    runtime.create_tenant(name="Acme", owner_user_id="owner")

    health = runtime.health()

    assert health["module"] == "multi_tenancy"
    assert health["status"] == "ok"
    assert health["stats"]["tenants"] == 1
    assert health["stats"]["memberships"] == 1
    assert health["stats"]["by_status"] == {"active": 1}
