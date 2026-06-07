def test_webhook_platform_default_config_is_enterprise_safe(rendered_webhook_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_webhook_platform["vendor"]

    config = vendor.build_default_config()

    assert config.enabled is True
    assert config.max_attempts == 3
    assert config.signature_header == "X-RapidKit-Signature"
