import pytest


def test_multi_tenancy_rejects_duplicate_slugs(rendered_multi_tenancy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_multi_tenancy["vendor"]
    runtime = vendor.MultiTenancy()

    runtime.create_tenant(name="Acme", slug="acme")

    with pytest.raises(vendor.MultiTenancyError, match="slug"):
        runtime.create_tenant(name="Acme Again", slug="acme")


def test_multi_tenancy_blocks_membership_on_suspended_tenant(rendered_multi_tenancy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_multi_tenancy["vendor"]
    runtime = vendor.MultiTenancy()
    tenant = runtime.create_tenant(name="Acme")
    runtime.set_status(tenant.id, vendor.TenantStatus.SUSPENDED)

    with pytest.raises(vendor.MultiTenancyError, match="not active"):
        runtime.assign_role(tenant_id=tenant.id, user_id="u-1")
