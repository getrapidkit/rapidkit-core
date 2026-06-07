def test_multi_tenancy_creates_tenant_owner_and_context(rendered_multi_tenancy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_multi_tenancy["vendor"]
    runtime = vendor.MultiTenancy()

    tenant = runtime.create_tenant(name="Acme Inc", owner_user_id="u-1")
    context = runtime.require_role(
        tenant_id=tenant.id,
        user_id="u-1",
        minimum_role=vendor.TenantRole.ADMIN,
    )

    assert tenant.slug == "acme-inc"
    assert context.isolation_key == f"tenant:{tenant.id}"
    assert context.role == vendor.TenantRole.OWNER
    assert len(runtime.audit_events(tenant.id)) == 2


def test_multi_tenancy_assigns_and_revokes_members(rendered_multi_tenancy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_multi_tenancy["vendor"]
    runtime = vendor.MultiTenancy()
    tenant = runtime.create_tenant(name="Tenant")

    membership = runtime.assign_role(
        tenant_id=tenant.id,
        user_id="u-2",
        role=vendor.TenantRole.MEMBER,
    )

    assert membership.role == vendor.TenantRole.MEMBER
    assert runtime.list_members(tenant.id) == [membership]
    assert runtime.revoke_member(tenant_id=tenant.id, user_id="u-2") is True
    assert runtime.list_members(tenant.id) == []
