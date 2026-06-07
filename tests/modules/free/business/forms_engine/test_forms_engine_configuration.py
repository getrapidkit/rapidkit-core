def test_forms_engine_config_defaults(rendered_forms_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_forms_engine["vendor"]
    config = vendor.FormsEngineConfig()

    assert config.enabled is True
