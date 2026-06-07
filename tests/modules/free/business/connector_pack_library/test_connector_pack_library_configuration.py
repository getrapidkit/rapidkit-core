def test_connector_pack_library_default_configuration(rendered_connector_pack_library) -> None:
    vendor = rendered_connector_pack_library["vendor"]
    config = vendor.build_default_config()

    assert config.enabled is True
    assert config.require_scopes is True
