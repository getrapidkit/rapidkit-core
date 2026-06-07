def test_rag_pipeline_default_config_is_enterprise_safe(rendered_rag_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_rag_pipeline["vendor"]

    config = vendor.build_default_config()

    assert config.enabled is True
    assert config.default_namespace == "default"
    assert config.chunk_overlap < config.chunk_size
    assert config.max_top_k == 10
    assert config.max_context_chars == 12_000
