from modules.free.tasks.event_bus import overrides


def test_event_bus_overrides_module_is_importable() -> None:
    assert overrides is not None
