def test_media_pipeline_override_module_is_importable() -> None:
    from modules.free.business.media_pipeline import overrides

    assert overrides is not None
