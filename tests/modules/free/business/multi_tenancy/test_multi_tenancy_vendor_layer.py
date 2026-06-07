def test_multi_tenancy_vendor_exports_runtime_contract(rendered_multi_tenancy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_multi_tenancy["vendor"]

    for name in (
        "MultiTenancy",
        "MultiTenancyConfig",
        "MultiTenancyError",
        "Tenant",
        "TenantMembership",
        "TenantContext",
        "TenantEvent",
        "TenantRole",
        "TenantStatus",
    ):
        assert hasattr(vendor, name)

    assert vendor.TenantRole.OWNER.value == "owner"
