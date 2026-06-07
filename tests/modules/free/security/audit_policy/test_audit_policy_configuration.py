def test_audit_policy_default_config_is_enterprise_safe(rendered_audit_policy) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_audit_policy["vendor"]

    config = vendor.build_default_config()

    assert config.enabled is True
    assert config.require_reason_by_default is True
    assert config.metadata == {}
