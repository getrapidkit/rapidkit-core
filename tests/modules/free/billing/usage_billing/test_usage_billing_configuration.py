def test_usage_billing_default_config_is_enterprise_safe(rendered_usage_billing) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_usage_billing["vendor"]

    config = vendor.build_default_config()

    assert config.enabled is True
    assert config.currency == "USD"
    assert config.metadata == {}
