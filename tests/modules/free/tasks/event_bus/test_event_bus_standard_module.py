def test_event_bus_generated_runtime_is_usable(rendered_event_bus) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_event_bus["vendor"]
    runtime = vendor.EventBus()
    assert runtime.health_check()["enabled"] is True
