import pytest


def test_multi_tenancy_rejects_disabled_runtime(rendered_multi_tenancy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_multi_tenancy["vendor"]
    runtime = vendor.MultiTenancy(vendor.MultiTenancyConfig(enabled=False))

    with pytest.raises(vendor.MultiTenancyError, match="disabled"):
        runtime.create_tenant(name="Nope")


def test_multi_tenancy_enforces_minimum_role(rendered_multi_tenancy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_multi_tenancy["vendor"]
    runtime = vendor.MultiTenancy()
    tenant = runtime.create_tenant(name="Acme")
    runtime.assign_role(tenant_id=tenant.id, user_id="viewer", role=vendor.TenantRole.VIEWER)

    with pytest.raises(vendor.MultiTenancyError, match="required tenant role"):
        runtime.require_role(
            tenant_id=tenant.id,
            user_id="viewer",
            minimum_role=vendor.TenantRole.ADMIN,
        )
