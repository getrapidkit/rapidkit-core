def test_event_bus_health_check(rendered_event_bus) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_event_bus["vendor"]
    runtime = vendor.EventBus()

    assert runtime.health_check()["module"] == "event_bus"
