def test_feature_flags_default_config_is_enterprise_safe(rendered_feature_flags) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_feature_flags["vendor"]

    config = vendor.build_default_config()

    assert config.enabled is True
    assert config.fail_closed is False
    assert config.metadata == {}
