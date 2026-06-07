def test_connector_hub_generated_runtime_is_usable(rendered_connector_hub) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_connector_hub["vendor"]

    hub = vendor.ConnectorHub()
    definition = hub.register_connector(vendor.ConnectorDefinition("x", "X", ("sync",)))

    assert definition.key == "x"
    assert hub.stats()["connectors"] == 1
