def test_multi_tenancy_generated_runtime_is_usable(rendered_multi_tenancy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_multi_tenancy["vendor"]

    runtime = vendor.MultiTenancy()
    tenant = runtime.create_tenant(name="Acme")

    assert tenant.id
    assert runtime.stats()["tenants"] == 1
