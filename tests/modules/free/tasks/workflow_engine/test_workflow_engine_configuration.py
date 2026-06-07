def test_workflow_engine_default_config_is_enterprise_safe(rendered_workflow_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_workflow_engine["vendor"]

    config = vendor.build_default_config()

    assert config.enabled is True
    assert config.max_steps == 50
    assert config.metadata == {}
