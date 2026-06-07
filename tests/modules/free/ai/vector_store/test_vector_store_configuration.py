def test_vector_store_default_config_is_enterprise_safe(rendered_vector_store) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_vector_store["vendor"]

    config = vendor.build_default_config()

    assert config.enabled is True
    assert config.default_namespace == "default"
    assert config.max_top_k == 50
    assert config.dimensions == 0
