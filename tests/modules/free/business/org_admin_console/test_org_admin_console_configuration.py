def test_org_admin_console_default_configuration(rendered_org_admin_console) -> None:
    vendor = rendered_org_admin_console["vendor"]
    config = vendor.build_default_config()

    assert config.enabled is True
    assert config.allowed_roles == ("owner", "admin", "member", "viewer")
