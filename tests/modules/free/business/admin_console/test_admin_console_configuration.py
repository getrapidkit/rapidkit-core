def test_admin_console_default_configuration(rendered_admin_console) -> None:
    vendor = rendered_admin_console["vendor"]
    config = vendor.build_default_config()

    assert config.enabled is True
    assert config.default_role == "admin"
