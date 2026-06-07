def test_support_center_default_configuration(rendered_support_center) -> None:
    vendor = rendered_support_center["vendor"]
    config = vendor.build_default_config()

    assert config.enabled is True
    assert config.default_sla_hours == 48
