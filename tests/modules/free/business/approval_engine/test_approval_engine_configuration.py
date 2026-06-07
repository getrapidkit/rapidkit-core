def test_approval_engine_default_configuration(rendered_approval_engine) -> None:
    vendor = rendered_approval_engine["vendor"]
    config = vendor.build_default_config()

    assert config.enabled is True
    assert config.default_required_role == "admin"
    assert config.require_reason is True
