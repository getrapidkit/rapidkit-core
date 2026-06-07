def test_event_bus_config_defaults(rendered_event_bus) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_event_bus["vendor"]
    config = vendor.EventBusConfig()

    assert config.enabled is True
