def test_event_bus_vendor_exports_contract(rendered_event_bus) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_event_bus["vendor"]

    for name in ("EventBus", "EventBusConfig", "EventBusError", "EventEnvelope", "EventStatus"):
        assert hasattr(vendor, name)
