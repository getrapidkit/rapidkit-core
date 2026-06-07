def test_multi_tenancy_default_config_is_enterprise_safe(rendered_multi_tenancy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_multi_tenancy["vendor"]

    config = vendor.build_default_config()

    assert config.enabled is True
    assert config.default_role == vendor.TenantRole.MEMBER
    assert config.allow_slug_updates is False
