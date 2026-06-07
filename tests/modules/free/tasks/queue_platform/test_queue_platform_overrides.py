def test_queue_platform_override_module_is_importable() -> None:
    from modules.free.tasks.queue_platform import overrides

    assert overrides is not None
