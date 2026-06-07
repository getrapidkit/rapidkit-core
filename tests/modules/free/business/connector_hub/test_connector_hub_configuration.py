def test_connector_hub_default_config_is_enterprise_safe(rendered_connector_hub) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_connector_hub["vendor"]

    config = vendor.build_default_config()

    assert config.enabled is True
    assert config.metadata == {}
