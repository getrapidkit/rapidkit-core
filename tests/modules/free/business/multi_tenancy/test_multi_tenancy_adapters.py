def test_multi_tenancy_resolves_tenant_by_slug_for_adapters(rendered_multi_tenancy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_multi_tenancy["vendor"]
    runtime = vendor.MultiTenancy()

    tenant = runtime.create_tenant(name="Launch Team", slug="Launch_Team")

    assert runtime.resolve_tenant("launch-team") == tenant
